from sqlalchemy import create_engine, text
from app.core.encryption import process_sensitive_fields
from app.models.models import DataSource
from app.core.database import SessionLocal
import logging
from typing import Dict, Any
import httpx
import asyncpg
import json

POSTGRES_TYPES = {"postgresql", "postgres"}
MYSQL_TYPES = {"mysql", "mariadb"}
HTTP_TYPES = {"rest_api", "http"}

logger = logging.getLogger(__name__)

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
    prefetched_outputs = {}
    pre_exec_ok = True

    # Only pre-execute traditional DB sources. 
    # API/HTTP sources should run in Deno to support dynamic params/methods.
    PRE_EXECUTABLE_TYPES = POSTGRES_TYPES | MYSQL_TYPES 

    for node in nodes_copy:
        # Resolve credentials first for EVERY node that has a connection_id
        connection_id = (node.get("props") or {}).get("connection_id", "")
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
                
                # Capture custom schema if specified in node props
                custom_schema = str(node["props"].get("schema", "") or "").strip()
                
                for cfg_key in ["host", "port", "username", "password", "database", "schema", "url", "email", "api_key", "token", "token_url", "client_id", "client_secret"]:
                    if cfg_key in resolved_cfg:
                        node["props"][cfg_key] = resolved_cfg[cfg_key]
                if ds.type:
                    node["props"]["connection_type"] = ds.type
                
                # Resolve schema hierarchically: Node Value > Connection Value > default
                conn_type = (node["props"].get("connection_type") or ds.type or "").lower()
                if custom_schema:
                    node["props"]["schema"] = custom_schema
                elif not node["props"].get("schema"):
                    if conn_type in POSTGRES_TYPES:
                        node["props"]["schema"] = "public"
                    else:
                        node["props"]["schema"] = ""
                        
                logger.info(f"[SourceExec] Credenciales resueltas desde DataSource '{ds.name}' para nodo {node['id']}")

        # Now decide if we pre-execute
        if node.get("toolType") not in ["sql_source", "sql_destination"] and node.get("category") != "source":
            continue
            
        conn_type = (node.get("props") or {}).get("connection_type", "").lower()
        if conn_type not in PRE_EXECUTABLE_TYPES:
            continue

        if websocket:
            await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "running"})
            await websocket.send_json({"type": "info", "message": f"[Fuente] Ejecutando '{node.get('label', node['id'])}' ..."})

        from datetime import datetime
        start_time = time.perf_counter()
        start_utc = datetime.utcnow().isoformat() + "Z"
        result = await execute_source_node(node)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        end_utc = datetime.utcnow().isoformat() + "Z"

        if result["success"]:
            prefetched_outputs[node["id"]] = {
                "rows": result["rows"],
                "duration": duration_ms,
                "start_utc": start_utc,
                "end_utc": end_utc
            }
            node["__pre_executed"] = True
            if websocket:
                await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "success"})
                await websocket.send_json({"type": "info", "message": f"[Fuente] {result['count']} registros cargados desde '{node.get('label', '')}' ({duration_ms}ms)"})
        else:
            node["__pre_executed"] = True
            if websocket:
                await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "error"})
                await websocket.send_json({"type": "error", "message": f"[Fuente Error] {result['error']}"})
            pre_exec_ok = False
            break

    flow_data["nodes"] = nodes_copy
    flow_data["prefetched_outputs"] = prefetched_outputs
    return pre_exec_ok, flow_data

