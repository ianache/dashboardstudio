import asyncio
import json
import logging
import os
import subprocess
from typing import Optional, Dict, Any

from app.services.ods_executor import ODSExecutor, ODSConfig, WriteMode, ods_executor

logger = logging.getLogger(__name__)

class DenoService:
    def __init__(self, runner_path: str = "app/runtime/runner.ts"):
        self.runner_path = runner_path
        # Use absolute path if possible or ensure it's relative to app root
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.full_runner_path = os.path.join(self.base_dir, "runtime", "runner.ts")

    async def check_runtime(self) -> Dict[str, Any]:
        """Check if Deno is installed and accessible."""
        try:
            process = await asyncio.create_subprocess_exec(
                "deno", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return {
                    "status": "ready",
                    "version": stdout.decode().strip().split("\n")[0],
                    "details": stdout.decode().strip()
                }
            return {
                "status": "error",
                "error": stderr.decode().strip()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def run_flow_test(self, script: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a simple script test in Deno."""
        test_payload = {
            "test_mode": True,
            "payload": {
                "script": script,
                "data": data or {}
            },
            "nodes": [],
            "connections": []
        }
        return await self.execute_deno(test_payload)

    async def run_flow(self, flow_data: Dict[str, Any], payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Run a full integration flow in Deno."""
        flow_payload = {
            **flow_data,
            "payload": payload or {}
        }
        result = await self.execute_deno(flow_payload)
        
        # Extract FINAL_RESULT if present in logs
        if result["status"] == "success" and result["logs"]:
            lines = result["logs"].split("\n")
            for line in reversed(lines):
                if line.startswith("FINAL_RESULT:"):
                    try:
                        result["result"] = json.loads(line[len("FINAL_RESULT:"):])
                        break
                    except:
                        pass
        return result

    async def run_flow_stream(self, flow_data: Dict[str, Any], payload: Optional[Dict] = None, db: Any = None):
        """
        Runs a flow in Deno and yields log messages.
        Uses subprocess.run via run_in_executor to avoid SelectorEventLoop
        limitations on Windows (asyncio.create_subprocess_exec raises
        NotImplementedError on Windows when uvicorn uses SelectorEventLoop).
        
        Args:
            flow_data: Flow configuration with nodes and connections
            payload: Initial payload data
            db: Database session for resolving data source connections (needed for ODS nodes)
        """
        if not os.path.exists(self.full_runner_path):
            yield {"type": "error", "message": f"Runner script not found at {self.full_runner_path}"}
            return

        import decimal
        import datetime
        
        def json_serial(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        flow_payload = {**flow_data, "payload": payload or {}}
        input_json = json.dumps(flow_payload, default=json_serial)

        logger.info(f"Launching Deno runner: {self.full_runner_path}")

        def _run_deno():
            return subprocess.run(
                [
                    "deno", "run",
                    "--allow-read",
                    "--allow-net",        # Required for rest_api / http nodes
                    "--allow-env",        # Required for reading environment variables
                    "--allow-sys",        # Required for node:os and similar builtins
                    self.full_runner_path
                ],
                input=input_json.encode(),
                capture_output=True,
                timeout=120,  # Increased from 30s to accommodate HTTP calls
            )

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _run_deno)
        except subprocess.TimeoutExpired:
            yield {"type": "error", "message": "Execution timed out after 30 seconds"}
            yield {"type": "status", "success": False, "exit_code": -1}
            return
        except FileNotFoundError:
            msg = "Deno not found. Please install Deno and ensure it is on PATH."
            logger.error(msg)
            yield {"type": "error", "message": msg}
            yield {"type": "status", "success": False, "exit_code": -1}
            return
        except Exception as e:
            msg = str(e) or repr(e) or f"Unknown error ({type(e).__name__})"
            logger.error(f"Error running Deno [{type(e).__name__}]: {repr(e)}")
            yield {"type": "error", "message": msg}
            yield {"type": "status", "success": False, "exit_code": -1}
            return

        stdout_text = result.stdout.decode(errors="replace")
        stderr_text = result.stderr.decode(errors="replace")

        if stderr_text.strip():
            logger.error(f"Deno stderr:\n{stderr_text.strip()}")

        # Stream stdout lines
        total_nodes = len(flow_data.get("nodes", []))
        nodes_processed = set()
        
        lines = stdout_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Handle EXEC_ODS signal (look ahead for payload)
            if line.startswith("EXEC_ODS:") and i + 1 < len(lines):
                parts = line.split(":")
                if len(parts) >= 5:
                    node_id = parts[1]
                    operation = parts[2]
                    connection_id = parts[3]
                    batch_id = parts[4]
                    
                    # Next line should be EXEC_ODS_PAYLOAD
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("EXEC_ODS_PAYLOAD:"):
                        i += 1  # Advance to payload line
                        try:
                            ods_payload = json.loads(next_line[len("EXEC_ODS_PAYLOAD:"):])
                            
                            # Yield status update
                            yield {
                                "type": "node_log",
                                "node_id": node_id,
                                "status": "running",
                                "message": f"Executing ODS {operation} operation"
                            }
                            
                            # Execute ODS operation if db session available
                            if db is not None:
                                result = await self._handle_ods_execution(ods_payload, db)
                                
                                # Yield result
                                yield {
                                    "type": "ods_result",
                                    "node_id": node_id,
                                    "batch_id": batch_id,
                                    "result": result
                                }
                                
                                # Update node status
                                if result["success"]:
                                    yield {"type": "node_status", "node_id": node_id, "status": "success"}
                                    nodes_processed.add(node_id)
                                else:
                                    yield {"type": "node_status", "node_id": node_id, "status": "error"}
                            else:
                                logger.warning(f"No db session available for ODS execution on node {node_id}")
                                yield {
                                    "type": "error",
                                    "message": f"No database session available for ODS execution"
                                }
                                yield {"type": "node_status", "node_id": node_id, "status": "error"}
                            
                            if total_nodes > 0:
                                progress = (len(nodes_processed) / total_nodes) * 100
                                yield {"type": "progress", "progress": round(progress, 2)}
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse EXEC_ODS_PAYLOAD: {e}")
                            yield {"type": "error", "message": f"Invalid EXEC_ODS payload: {e}"}
                        except Exception as e:
                            logger.error(f"ODS execution error: {e}")
                            yield {"type": "error", "message": f"ODS execution failed: {e}"}
                            yield {"type": "node_status", "node_id": node_id, "status": "error"}
            
            # Handle existing signals (NODE_STATUS, NODE_LOG_JSON, FINAL_RESULT)
            elif line.startswith("NODE_STATUS:"):
                parts = line.split(":")
                if len(parts) >= 3:
                    node_id = parts[1]
                    status = parts[2]
                    yield {"type": "node_status", "node_id": node_id, "status": status}
                    
                    if status in ["success", "error"]:
                        nodes_processed.add(node_id)
                        if total_nodes > 0:
                            progress = (len(nodes_processed) / total_nodes) * 100
                            yield {"type": "progress", "progress": round(progress, 2)}
                            
            elif line.startswith("NODE_LOG_JSON:"):
                try:
                    data = json.loads(line[len("NODE_LOG_JSON:"):])
                    node_id = data.get("node_id")
                    status = data.get("status")
                    
                    yield {
                        "type": "node_log", 
                        "node_id": node_id, 
                        "status": status,
                        "input": data.get("input"),
                        "output": data.get("output"),
                        "duration": data.get("duration", 0)
                    }
                    
                    if status in ["success", "error"]:
                        nodes_processed.add(node_id)
                        if total_nodes > 0:
                            progress = (len(nodes_processed) / total_nodes) * 100
                            yield {"type": "progress", "progress": round(progress, 2)}
                except Exception:
                    pass
                    
            elif line.startswith("FINAL_RESULT:"):
                try:
                    res = json.loads(line[len("FINAL_RESULT:"):])
                    yield {"type": "result", "data": res}
                except Exception:
                    yield {"type": "info", "message": line}
            else:
                yield {"type": "info", "message": line}
            
            i += 1

        # Stream stderr lines as error messages to the client
        for line in stderr_text.splitlines():
            line = line.strip()
            if line:
                yield {"type": "error", "message": line}

        yield {"type": "status", "success": result.returncode == 0, "exit_code": result.returncode}


    async def execute_deno(self, flow_data: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
        """Run Deno with the provided flow data."""
        if not os.path.exists(self.full_runner_path):
            return {"status": "error", "error": f"Runner script not found at {self.full_runner_path}"}

        try:
            # Deno security flags
            flags = [
                "run",
                "--no-remote",
                "--allow-read",
                "--v8-flags=--max-old-space-size=256",
                self.full_runner_path
            ]

            process = await asyncio.create_subprocess_exec(
                "deno", *flags,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            input_json = json.dumps(flow_data)
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_json.encode()),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {"status": "error", "error": "Execution timed out"}

            output = stdout.decode().strip()
            error_output = stderr.decode().strip()

            return {
                "status": "success" if process.returncode == 0 else "error",
                "exit_code": process.returncode,
                "logs": output,
                "errors": error_output
            }

        except Exception as e:
            logger.error(f"Error executing Deno: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _handle_ods_execution(
        self, 
        payload: Dict[str, Any], 
        db: Any
    ) -> Dict[str, Any]:
        """
        Handle EXEC_ODS signal by delegating to ODSExecutor.
        
        Args:
            payload: The EXEC_ODS_PAYLOAD JSON data
            db: Database session for resolving connection credentials
            
        Returns:
            Dict with execution results
        """
        import asyncpg
        from app.models.models import DataSource
        from app.core.encryption import process_sensitive_fields
        import json
        
        logger.info(f"Handling EXEC_ODS for node {payload.get('node_id')}")
        
        try:
            # Extract configuration
            target = payload['target']
            config_data = payload['config']
            records = payload['data']
            
            config = ODSConfig(
                connection_id=target['connection_id'],
                schema=target['schema'],
                table=target['table'],
                write_mode=WriteMode(config_data['write_mode']),
                identity_fields=config_data.get('identity_fields', []),
                batch_size=config_data.get('batch_size', 1000)
            )
            
            # Resolve connection credentials from database
            ds = db.query(DataSource).filter(DataSource.id == config.connection_id).first()
            if not ds:
                raise ValueError(f"Connection {config.connection_id} not found")
            
            # Parse connection config
            try:
                raw_config = json.loads(ds.connection_url)
            except Exception:
                raw_config = {"url": ds.connection_url}
            
            config_dict = process_sensitive_fields(raw_config, action="decrypt")
            
            # Build connection string for PostgreSQL
            if config_dict.get('type') == 'database' or 'host' in config_dict:
                host = config_dict.get('host', 'localhost')
                port = config_dict.get('port', 5432)
                user = config_dict.get('username', '')
                password = config_dict.get('password', '')
                database = config_dict.get('database', '')
                connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                raise ValueError(f"Unsupported connection type for ODS: {config_dict.get('type')}")
            
            # Execute with connection
            conn = await asyncpg.connect(dsn=connection_string)
            try:
                result = await ods_executor.execute(config, records, conn)
                
                return {
                    "success": result.success,
                    "complete_success": result.complete_success,
                    "rows_affected": result.rows_affected,
                    "rows_inserted": result.rows_inserted,
                    "rows_updated": result.rows_updated,
                    "batches_total": result.batches_total,
                    "batches_successful": result.batches_successful,
                    "batches_failed": result.batches_failed,
                    "errors": [
                        {
                            "batch_number": e.batch_number,
                            "error_type": e.error_type,
                            "message": e.message,
                            "record_index": e.record_index
                        }
                        for e in result.errors
                    ],
                    "duration_ms": result.duration_ms
                }
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"ODS execution failed: {e}")
            return {
                "success": False,
                "complete_success": False,
                "rows_affected": 0,
                "rows_inserted": 0,
                "rows_updated": 0,
                "batches_total": 0,
                "batches_successful": 0,
                "batches_failed": 0,
                "errors": [{"error_type": "ExecutionError", "message": str(e)}],
                "duration_ms": 0
            }


# Singleton instance
deno_service = DenoService()
