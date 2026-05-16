import logging
from typing import Dict, Any, List
import asyncpg
from app.core.database import SessionLocal
from app.models.models import DataSource
from app.core.encryption import process_sensitive_fields
import json

logger = logging.getLogger(__name__)

async def post_execute_flow_nodes(flow_data: Dict[str, Any], node_logs: List[Dict[str, Any]], db):
    """
    Post-execution for destination nodes (like ods_pg) that need Python-side execution
    after the Deno sandbox flow completes.
    """
    nodes = {n["id"]: n for n in flow_data.get("nodes", [])}
    
    for log in node_logs:
        node_id = log.get("node_id")
        node = nodes.get(node_id)
        if not node:
            continue
            
        tool_type = node.get("toolType")
        if tool_type == "ods_pg" and log.get("status") == "success":
            input_data = log.get("input", {})
            
            # Extract records from input data
            records = []
            if isinstance(input_data, dict):
                if "data" in input_data and isinstance(input_data["data"], list):
                    records = input_data["data"]
                elif "rows" in input_data and isinstance(input_data["rows"], list):
                    records = input_data["rows"]
                else:
                    records = [input_data]
            elif isinstance(input_data, list):
                records = input_data

            if not records:
                log["output"] = {"status": "skipped", "message": "No data to insert"}
                continue

            props = node.get("props", {})
            conn_id = props.get("connection_id")
            if not conn_id:
                log["status"] = "error"
                log["output"] = {"error": "connection_id is missing"}
                continue
                
            ds = db.query(DataSource).filter(DataSource.id == conn_id).first()
            if not ds:
                log["status"] = "error"
                log["output"] = {"error": "DataSource not found"}
                continue

            try:
                raw_config = json.loads(ds.connection_url)
            except Exception:
                raw_config = {"url": ds.connection_url}
            config = process_sensitive_fields(raw_config, action="decrypt")
            
            host = config.get("host", "localhost")
            port = config.get("port", 5432)
            user = config.get("username", "")
            password = config.get("password", "")
            database = config.get("database", "")
            
            schema = props.get("schema", "public")
            table = props.get("table", "")
            write_mode = props.get("write_mode", "append")
            identity_fields = props.get("identity_fields", [])
            # batch_size = int(props.get("batch_size", 1000)) # batch logic can be added later if needed
            
            if not table:
                log["status"] = "error"
                log["output"] = {"error": "Table not specified"}
                continue
            
            logger.info(f"[DestinationExec] Executing ods_pg node {node_id} on {host}:{port}/{database} ({write_mode})")
            
            try:
                conn = await asyncpg.connect(
                    user=user, password=password, database=database, host=host, port=port, timeout=15
                )
                try:
                    # Construct query
                    columns = list(records[0].keys())
                    cols_quoted = [f'"{c}"' for c in columns]
                    placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
                    
                    if write_mode == "overwrite":
                        await conn.execute(f'TRUNCATE TABLE "{schema}"."{table}"')
                        
                    vals = [[r.get(c) for c in columns] for r in records]
                    
                    if write_mode == "upsert" and identity_fields:
                        conflict_cols = ", ".join(f'"{c}"' for c in identity_fields)
                        update_cols = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in columns if c not in identity_fields)
                        
                        if update_cols:
                            query = f'INSERT INTO "{schema}"."{table}" ({", ".join(cols_quoted)}) VALUES ({placeholders}) ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_cols}'
                        else:
                            query = f'INSERT INTO "{schema}"."{table}" ({", ".join(cols_quoted)}) VALUES ({placeholders}) ON CONFLICT ({conflict_cols}) DO NOTHING'
                        
                        await conn.executemany(query, vals)
                    else:
                        query = f'INSERT INTO "{schema}"."{table}" ({", ".join(cols_quoted)}) VALUES ({placeholders})'
                        await conn.executemany(query, vals)
                        
                    log["output"] = {"status": "success", "rows_affected": len(records), "mode": write_mode}
                finally:
                    await conn.close()
            except Exception as e:
                logger.error(f"[DestinationExec] Error in ods_pg: {e}")
                log["status"] = "error"
                log["output"] = {"error": str(e)}

    return node_logs
