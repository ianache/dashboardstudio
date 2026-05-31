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

    if conn_type in POSTGRES_TYPES:
        return await _execute_postgres(props, label)
    elif conn_type in MYSQL_TYPES:
        return await _execute_mysql(props, label)
    elif conn_type in HTTP_TYPES:
        return await _execute_http(props, label)
    
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

def _err(msg: str) -> Dict:
    return {"success": False, "rows": [], "count": 0, "error": msg}

async def pre_execute_flow_nodes(flow_data: Dict[str, Any], db, websocket=None) -> tuple[bool, Dict[str, Any]]:
    import copy
    import time
    nodes_copy = copy.deepcopy(flow_data.get("nodes", []))
    connections = flow_data.get("connections", [])
    prefetched_outputs = {}
    pre_exec_ok = True

    # Identify nodes that MUST be pre-executed
    def is_pre_executable(n):
        return n.get("toolType") in ["llm", "pickle_model", "sql_source", "sql_destination"] or n.get("category") == "source"

    # Sort nodes topologically to respect dependencies during pre-execution
    # (Simple Kahn implementation for pre-execution subset)
    try:
        from app.runtime.runner import get_topological_order
        # Mock FlowNode objects for the runner helper if needed, 
        # but the helper works with Dict if IDs and connections match.
        sorted_nodes = get_topological_order(nodes_copy, connections)
    except Exception as e:
        logger.warning(f"[SourceExec] Could not sort nodes for pre-execution: {e}")
        sorted_nodes = nodes_copy

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
                
                for cfg_key in ["host", "port", "username", "password", "database", "schema", "url", "email", "api_key", "token", "token_url", "client_id", "client_secret", "model"]:
                    if cfg_key in resolved_cfg:
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

        if websocket:
            await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "running"})
            label = node.get('label', node['id'])
            msg_prefix = "[IA]" if is_llm else ("[ML]" if is_ml else "[Fuente]")
            await websocket.send_json({"type": "info", "message": f"{msg_prefix} Ejecutando '{label}' ..."})

        from datetime import datetime
        start_time = time.perf_counter()
        start_utc = datetime.utcnow().isoformat() + "Z"
        
        if is_llm:
            # Pass ctx-like structure (payload + variables)
            ctx = {"payload": input_payload, "variables": flow_data.get("variables", {})}
            result = await execute_llm_node(node["props"], ctx)
            if result["success"]: result["rows"] = result["output"]
        elif is_ml:
            result = await execute_ml_node(node["props"], input_payload, db)
            if result["success"]: result["rows"] = result["output"]
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

