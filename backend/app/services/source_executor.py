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
    schema = props.get("schema", "public")
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

