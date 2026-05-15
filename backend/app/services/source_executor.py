"""
Source Node Executor
====================
Python executes source nodes (DB queries, REST calls) BEFORE handing the
flow to Deno. This avoids the need to give Deno network access and keeps
credential handling entirely inside the trusted Python layer.

Supported connection types
--------------------------
  postgresql / postgres / database / mssql / oracle -> asyncpg (TCP SQL)
  mysql / mariadb                                   -> aiomysql (if installed)
  rest_api / http / jwt                             -> httpx async GET/POST
"""

import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Types that route to the PostgreSQL executor (asyncpg wire protocol)
POSTGRES_TYPES = {"postgresql", "postgres", "database", "mssql", "oracle"}
MYSQL_TYPES    = {"mysql", "mariadb"}
HTTP_TYPES     = {"rest_api", "http", "jwt"}


async def execute_source_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a source node and return a result dict:
        { success: bool, rows: list[dict], count: int, error: str | None }
    """
    props      = node.get("props") or {}
    conn_type  = props.get("connection_type", "").lower()

    if conn_type in POSTGRES_TYPES:
        return await _exec_postgres(node["id"], node.get("label", ""), props)
    elif conn_type in MYSQL_TYPES:
        return await _exec_mysql(node["id"], node.get("label", ""), props)
    elif conn_type in HTTP_TYPES:
        return await _exec_http(node["id"], node.get("label", ""), props)
    else:
        return _err(f"Sin ejecutor para tipo de conexión: '{conn_type}'")


# ── PostgreSQL ──────────────────────────────────────────────────────────────────

async def _exec_postgres(node_id: str, label: str, props: Dict) -> Dict:
    try:
        import asyncpg
    except ImportError:
        return _err("asyncpg no está instalado en el entorno")

    host     = props.get("host", "localhost")
    port     = int(props.get("port") or 5432)
    user     = props.get("username", "")
    password = props.get("password", "")
    database = props.get("database", "")
    schema   = props.get("schema", "public")
    table    = props.get("table", "")
    query    = props.get("query", "")
    limit    = int(props.get("limit") or 1000)

    # Build SQL
    if query.strip():
        sql = query.strip()
    elif table.strip():
        full_table = f'"{schema}"."{table}"' if schema else f'"{table}"'
        sql = f"SELECT * FROM {full_table} LIMIT {limit}"
    else:
        return _err("El nodo fuente no tiene 'query' ni 'table' configurado")

    logger.info(f"[SourceExec][{label}] PostgreSQL → {host}:{port}/{database}  SQL: {sql[:120]}")

    try:
        conn = await asyncpg.connect(
            host=host, port=port,
            user=user, password=password,
            database=database,
            timeout=15,
        )
        try:
            rows = await conn.fetch(sql)
            data = [_record_to_dict(r) for r in rows]
            logger.info(f"[SourceExec][{label}] OK — {len(data)} filas")
            return {"success": True, "rows": data, "count": len(data), "error": None}
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"[SourceExec][{label}] PostgreSQL error: {e}")
        return _err(str(e))


def _record_to_dict(record) -> dict:
    """Convert asyncpg Record to a JSON-serialisable dict."""
    import decimal, datetime
    out = {}
    for key in record.keys():
        val = record[key]
        if isinstance(val, decimal.Decimal):
            val = float(val)
        elif isinstance(val, (datetime.date, datetime.datetime)):
            val = val.isoformat()
        out[key] = val
    return out


# ── MySQL ───────────────────────────────────────────────────────────────────────

async def _exec_mysql(node_id: str, label: str, props: Dict) -> Dict:
    try:
        import aiomysql
    except ImportError:
        return _err("aiomysql no está instalado en el entorno")

    host     = props.get("host", "localhost")
    port     = int(props.get("port") or 3306)
    user     = props.get("username", "")
    password = props.get("password", "")
    database = props.get("database", "")
    table    = props.get("table", "")
    query    = props.get("query", "")
    limit    = int(props.get("limit") or 1000)

    sql = query.strip() if query.strip() else f"SELECT * FROM `{table}` LIMIT {limit}"
    if not sql:
        return _err("El nodo fuente no tiene 'query' ni 'table' configurado")

    logger.info(f"[SourceExec][{label}] MySQL → {host}:{port}/{database}")
    try:
        conn = await aiomysql.connect(
            host=host, port=port,
            user=user, password=password,
            db=database, connect_timeout=15,
        )
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql)
                rows = await cur.fetchall()
                data = [dict(r) for r in rows]
            return {"success": True, "rows": data, "count": len(data), "error": None}
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"[SourceExec][{label}] MySQL error: {e}")
        return _err(str(e))


# ── HTTP / REST API ─────────────────────────────────────────────────────────────

async def _exec_http(node_id: str, label: str, props: Dict) -> Dict:
    try:
        import httpx
    except ImportError:
        return _err("httpx no está instalado en el entorno")

    url      = props.get("url", "")
    username = props.get("username", "")
    password = props.get("password", "")
    api_key  = props.get("api_key", "")
    token    = props.get("token", "")

    if not url:
        return _err("El nodo fuente no tiene 'url' configurada")

    headers: Dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif token:
        headers["Authorization"] = f"Bearer {token}"

    auth = (username, password) if username and password else None

    logger.info(f"[SourceExec][{label}] HTTP GET → {url[:80]}")
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            resp = await client.get(url, auth=auth)
            resp.raise_for_status()
            body = resp.json()
            rows = body if isinstance(body, list) else [body]
            return {"success": True, "rows": rows, "count": len(rows), "error": None}
    except Exception as e:
        logger.error(f"[SourceExec][{label}] HTTP error: {e}")
        return _err(str(e))


# ── Helper ──────────────────────────────────────────────────────────────────────

def _err(msg: str) -> Dict:
    return {"success": False, "rows": [], "count": 0, "error": msg}
