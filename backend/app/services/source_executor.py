from sqlalchemy import create_engine, text
from app.core.encryption import process_sensitive_fields
from app.models.models import DataSource
from app.core.database import SessionLocal
import logging
from typing import Dict, Any
import httpx
import asyncpg
import json

from app.services.llm_executor import execute_llm_node
from app.services.ml_executor import execute_ml_node
from app.services.ods_executor import ODSConfig, WriteMode, ods_executor

POSTGRES_TYPES = {"postgresql", "postgres"}
MYSQL_TYPES = {"mysql", "mariadb"}
HTTP_TYPES = {"rest_api", "http"}

logger = logging.getLogger(__name__)

# List of sensitive keys to remove from node props after pre-execution
SENSITIVE_KEYS = ["password", "api_key", "token", "client_secret"]

def get_db_engine(data_source: DataSource):
    try:
        raw_config = json.loads(data_source.connection_url)
    except Exception:
        raw_config = {"url": data_source.connection_url}
    config = process_sensitive_fields(raw_config, action="decrypt")
    
    # Generic connection string builder based on type
    # Supports: postgresql, mysql, mssql, sqlite
    if config['type'] == 'database':
        # Connection string format: dialect+driver://username:password@host:port/database
        # Assuming postgresql for now if not specified, but flexible
        url = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        return create_engine(url)
    
    raise ValueError(f"Unsupported DB type: {config['type']}")

def execute_sql(connection_id: str, query: str):
    db = SessionLocal()
    try:
        ds = db.query(DataSource).filter(DataSource.id == connection_id).first()
        if not ds:
            raise ValueError("Connection not found")
            
        engine = get_db_engine(ds)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            conn.commit()
            return {"status": "success"}
    finally:
        db.close()

async def execute_source_node(node: Dict[str, Any]) -> Dict[str, Any]:
    props = node.get("props") or {}
    conn_type = props.get("connection_type", "").lower()
    label = node.get("label", node["id"])
    tool_type = node.get("toolType", "")

    if conn_type in POSTGRES_TYPES:
        return await _execute_postgres(props, label)
    elif conn_type in MYSQL_TYPES:
        return await _execute_mysql(props, label)
    elif conn_type in HTTP_TYPES:
        return await _execute_http(props, label)
    elif tool_type == "csv_file" and conn_type == "s3":
        return await _execute_csv_s3(props, label)
    elif tool_type == "csv_file":
        return await _execute_csv_local(props, label)

    return _err(f"Tipo de conexión no soportado: {conn_type}")

async def _execute_postgres(props: Dict, label: str) -> Dict:
    host = props.get("host", "localhost")
    port = props.get("port", "5432")
    user = props.get("username", "")
    password = props.get("password", "")
    database = props.get("database", "")
    schema = props.get("schema") or "public"
    table = props.get("table", "")
    custom_query = props.get("query", "").strip()

    query = custom_query
    if not query:
        if not table:
            return _err("No se especificó tabla ni query SQL")
        # Identifiers quoted for safety
        query = f'SELECT * FROM "{schema}"."{table}" LIMIT 1000'

    logger.info(f"[SourceExec][PostgreSQL] {host}:{port}/{database}  SQL: {query}")
    try:
        conn = await asyncpg.connect(
            user=user, password=password, database=database, host=host, port=port, timeout=15
        )
        try:
            records = await conn.fetch(query)
            rows = [dict(r) for r in records]
            return {"success": True, "rows": rows, "count": len(rows), "error": None}
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"[SourceExec][PostgreSQL] Error: {e}")
        return _err(str(e))

async def _execute_mysql(props: Dict, label: str) -> Dict:
    host = props.get("host", "localhost")
    port = int(props.get("port", 3306))
    user = props.get("username", "")
    password = props.get("password", "")
    database = props.get("database", "")
    table = props.get("table", "")
    custom_query = props.get("query", "").strip()

    query = custom_query
    if not query:
        if not table:
            return _err("No se especificó tabla ni query SQL")
        query = f"SELECT * FROM `{table}` LIMIT 1000"

    try:
        import aiomysql
        conn = await aiomysql.connect(
            host=host, port=port, user=user, password=password, db=database, connect_timeout=15
        )
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query)
                rows = await cur.fetchall()
                return {"success": True, "rows": list(rows), "count": len(rows), "error": None}
        finally:
            conn.close()
    except ImportError:
        return _err("La librería aiomysql no está instalada. Ejecute 'uv add aiomysql' para conectarse a MySQL.")
    except Exception as e:
        return _err(str(e))

async def _execute_http(props: Dict, label: str) -> Dict:
    url = props.get("url", "")
    if not url:
        return _err("No url configurada")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            rows = data if isinstance(data, list) else [data]
            return {"success": True, "rows": rows, "count": len(rows), "error": None}
    except Exception as e:
        return _err(str(e))

async def _execute_csv_local(props: Dict, label: str) -> Dict:
    import pandas as pd
    import os
    path = props.get("path", "").strip()
    if not path:
        return _err("No se especificó la ruta del archivo")
    if not os.path.exists(path):
        return _err(f"Archivo no encontrado: {path}")
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xls", ".xlsm"):
            df = pd.read_excel(path, dtype=str)
        else:
            delimiter = props.get("delimiter") or ","
            has_header = props.get("has_header", "true") != "false"
            encoding = props.get("encoding") or "UTF-8"
            df = pd.read_csv(path, sep=delimiter, header=0 if has_header else None,
                             encoding=encoding, dtype=str)
        df = df.where(pd.notna(df), None)
        rows = df.to_dict(orient="records")
        return {"success": True, "rows": rows, "count": len(rows), "error": None}
    except Exception as e:
        return _err(f"Error leyendo archivo: {str(e)}")


async def _execute_csv_s3(props: Dict, label: str) -> Dict:
    import boto3
    import io
    import pandas as pd
    bucket = props.get("bucket", "").strip()
    path = props.get("path", "").strip().lstrip("/")
    access_key = props.get("access_key", "")
    secret_key = props.get("secret_key", "")
    region = props.get("region") or "us-east-1"
    if not bucket or not path:
        return _err("Se requiere bucket y ruta del archivo para S3")
    try:
        s3 = boto3.client("s3", region_name=region,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
        obj = s3.get_object(Bucket=bucket, Key=path)
        body = obj["Body"].read()
        ext = path.rsplit(".", 1)[-1].lower()
        if ext in ("xlsx", "xls", "xlsm"):
            df = pd.read_excel(io.BytesIO(body), dtype=str)
        else:
            delimiter = props.get("delimiter") or ","
            has_header = props.get("has_header", "true") != "false"
            encoding = props.get("encoding") or "UTF-8"
            df = pd.read_csv(io.BytesIO(body), sep=delimiter,
                             header=0 if has_header else None,
                             encoding=encoding, dtype=str)
        df = df.where(pd.notna(df), None)
        rows = df.to_dict(orient="records")
        return {"success": True, "rows": rows, "count": len(rows), "error": None}
    except Exception as e:
        return _err(f"Error leyendo S3 s3://{bucket}/{path}: {str(e)}")


def _err(msg: str) -> Dict:
    return {"success": False, "rows": [], "count": 0, "error": msg}

async def _pre_execute_ods_node(props: Dict, records: Any, db) -> Dict:
    """Pre-execute an ods_pg node: writes records to PostgreSQL and returns them
    as output so downstream nodes (e.g. pickle_model) can consume the same rows."""
    if not isinstance(records, list) or not records:
        return {"success": False, "error": "ODS requires a non-empty list of records as input", "rows": []}

    table = props.get("table", "")
    if not table:
        return {"success": False, "error": "No table configured for ODS node", "rows": []}

    schema = props.get("schema") or "public"
    write_mode_str = (props.get("write_mode") or "append").lower()
    try:
        write_mode = WriteMode(write_mode_str)
    except ValueError:
        write_mode = WriteMode.APPEND

    config = ODSConfig(
        connection_id=props.get("connection_id", ""),
        schema=schema,
        table=table,
        write_mode=write_mode,
        identity_fields=props.get("identity_fields") or [],
        batch_size=int(props.get("batch_size") or 1000),
    )

    host = props.get("host", "localhost")
    port = int(props.get("port") or 5432)
    user = props.get("username", "")
    password = props.get("password", "")
    database = props.get("database", "")

    try:
        conn = await asyncpg.connect(
            user=user, password=password, database=database,
            host=host, port=port, timeout=15
        )
        try:
            result = await ods_executor.execute(config, records, conn, db=db)
            if result.success:
                return {"success": True, "rows": records, "rows_written": result.rows_affected}
            errs = "; ".join(e.message for e in (result.errors or [])[:3])
            return {"success": False, "error": f"ODS write failed: {errs or 'Unknown'}", "rows": []}
        finally:
            await conn.close()
    except Exception as e:
        return {"success": False, "error": f"ODS connection error: {str(e)}", "rows": []}

async def pre_execute_flow_nodes(flow_data: Dict[str, Any], db, websocket=None) -> tuple[bool, Dict[str, Any]]:
    import copy
    import time
    nodes_copy = copy.deepcopy(flow_data.get("nodes", []))
    connections = flow_data.get("connections", [])
    prefetched_outputs = {}
    pre_exec_ok = True

    # Identify nodes that MUST be pre-executed
    def is_pre_executable(n):
        return n.get("toolType") in ["llm", "pickle_model", "sql_source", "sql_destination", "ods_pg"] or n.get("category") == "source"

    # Sort nodes topologically (Kahn's algorithm) so that source/LLM nodes
    # that feed into other pre-executable nodes are processed first.
    def _kahn_sort(nodes, conns):
        ids = [n["id"] for n in nodes]
        in_deg = {nid: 0 for nid in ids}
        adj = {nid: [] for nid in ids}
        for c in conns:
            s, t = c.get("from"), c.get("to")
            if s in adj and t in in_deg:
                adj[s].append(t)
                in_deg[t] += 1
        queue = [nid for nid in ids if in_deg[nid] == 0]
        order = []
        while queue:
            u = queue.pop(0)
            order.append(u)
            for v in adj[u]:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    queue.append(v)
        if len(order) < len(nodes):
            return nodes  # cycle detected, fall back to original order
        nm = {n["id"]: n for n in nodes}
        return [nm[nid] for nid in order]

    sorted_nodes = _kahn_sort(nodes_copy, connections)

    for node in sorted_nodes:
        # Only process pre-executable nodes
        if not is_pre_executable(node):
            continue

        # 1. Resolve credentials (existing logic)
        props = node.get("props") or {}
        connection_id = props.get("connection_id")
        
        if connection_id:
            ds = db.query(DataSource).filter(DataSource.id == connection_id).first()
            if ds:
                try:
                    raw_config = json.loads(ds.connection_url)
                except Exception:
                    raw_config = {"url": ds.connection_url}
                resolved_cfg = process_sensitive_fields(raw_config, action="decrypt")
                
                if not node.get("props"):
                    node["props"] = {}
                
                # Credentials always come from DataSource (security).
                # Structural props (schema) only fill in if the node has no user-set value.
                NODE_OVERRIDABLE = {"schema", "database", "model"}
                for cfg_key in ["host", "port", "username", "password", "database", "schema", "url", "email", "api_key", "token", "token_url", "client_id", "client_secret", "model"]:
                    if cfg_key in resolved_cfg:
                        if cfg_key in NODE_OVERRIDABLE and node["props"].get(cfg_key):
                            continue  # keep the user's value
                        node["props"][cfg_key] = resolved_cfg[cfg_key]
                if ds.type:
                    node["props"]["connection_type"] = ds.type

        # 2. Prepare dynamic input (Chaining improvement)
        # Check if this node has an incoming connection from another PRE-EXECUTED node
        input_payload = flow_data.get("payload", {}) # Default to initial payload
        incoming = [c for c in connections if c.get("to") == node["id"]]
        
        if incoming:
            # If multiple inputs, we merge or take the first successful pre-executed one
            # For v1.9, we'll take the output of the first connected pre-executed node
            for conn in incoming:
                prev_id = conn.get("from")
                if prev_id in prefetched_outputs:
                    input_payload = prefetched_outputs[prev_id].get("rows", [])
                    logger.info(f"[SourceExec] Node {node['id']} consuming output from pre-executed node {prev_id}")
                    break

        # 3. Execution
        is_llm = node.get("toolType") == "llm"
        is_ml  = node.get("toolType") == "pickle_model"
        is_ods = node.get("toolType") == "ods_pg"

        if websocket:
            await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "running"})
            label = node.get('label', node['id'])
            msg_prefix = "[IA]" if is_llm else ("[ML]" if is_ml else ("[ODS]" if is_ods else "[Fuente]"))
            await websocket.send_json({"type": "info", "message": f"{msg_prefix} Ejecutando '{label}' ..."})

        from datetime import datetime
        start_time = time.perf_counter()
        start_utc = datetime.utcnow().isoformat() + "Z"

        if is_llm:
            # Build variables dict from metadata.variables (list of {name, type, value})
            raw_vars = flow_data.get("metadata", {}).get("variables", [])
            if isinstance(raw_vars, list):
                variables_dict = {}
                for v in raw_vars:
                    val = v.get("value")
                    vtype = v.get("type", "string")
                    if vtype == "number":
                        try: val = float(val)
                        except (TypeError, ValueError): pass
                    elif vtype == "boolean":
                        val = str(val).lower() == "true"
                    elif vtype == "json":
                        try: val = json.loads(val)
                        except Exception: pass
                    if v.get("name"):
                        variables_dict[v["name"]] = val
            else:
                variables_dict = raw_vars if isinstance(raw_vars, dict) else {}
            ctx = {"payload": input_payload, "variables": variables_dict}
            result = await execute_llm_node(node["props"], ctx)
            if result["success"]: result["rows"] = result["output"]
        elif is_ml:
            result = await execute_ml_node(node["props"], input_payload, db)
            if result["success"]: result["rows"] = result["output"]
        elif is_ods:
            result = await _pre_execute_ods_node(node["props"], input_payload, db)
        else:
            result = await execute_source_node(node)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        end_utc = datetime.utcnow().isoformat() + "Z"

        if result["success"]:
            prefetched_outputs[node["id"]] = {
                "rows": result.get("rows", result.get("output")),
                "duration": duration_ms,
                "start_utc": start_utc,
                "end_utc": end_utc,
                "warning": result.get("warning")
            }
            node["__pre_executed"] = True
            
            # Scrub credentials
            props = node.get("props", {})
            for key in SENSITIVE_KEYS:
                if key in props: del props[key]

            if websocket:
                await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "success"})
                label = node.get('label', '')
                if is_llm:
                    await websocket.send_json({"type": "info", "message": f"[IA] Completado para '{label}' ({duration_ms}ms)"})
                elif is_ml:
                    warn_suffix = f" (Aviso: {result['warning']})" if result.get('warning') else ""
                    await websocket.send_json({"type": "info", "message": f"[ML] Inferencia completada para '{label}' ({duration_ms}ms){warn_suffix}"})
                else:
                    await websocket.send_json({"type": "info", "message": f"[Fuente] {result['count']} registros cargados desde '{label}' ({duration_ms}ms)"})
        else:
            node["__pre_executed"] = True
            if websocket:
                await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "error"})
                err_msg = result.get('error', 'Error desconocido')
                prefix = 'IA' if is_llm else ('ML' if is_ml else 'Fuente')
                await websocket.send_json({"type": "error", "message": f"[{prefix} Error] {err_msg}"})
            pre_exec_ok = False
            break

    flow_data["nodes"] = nodes_copy
    flow_data["prefetched_outputs"] = prefetched_outputs
    return pre_exec_ok, flow_data

