import asyncio
import json
import logging
import os
import subprocess
from typing import Optional, Dict, Any

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

    async def run_flow_stream(self, flow_data: Dict[str, Any], payload: Optional[Dict] = None):
        """
        Runs a flow in Deno and yields log messages.
        Uses subprocess.run via run_in_executor to avoid SelectorEventLoop
        limitations on Windows (asyncio.create_subprocess_exec raises
        NotImplementedError on Windows when uvicorn uses SelectorEventLoop).
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
                ["deno", "run", "--no-remote", "--allow-read", self.full_runner_path],
                input=input_json.encode(),
                capture_output=True,
                timeout=30,
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
        execution_id = None # Should be passed from the scheduler
        
        # Helper to extract execution_id from scope if possible
        # For now, let's assume we pass execution_id to the runner or it's provided by context
        
        for line in stdout_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("NODE_STATUS:"):
                parts = line.split(":")
                if len(parts) >= 3:
                    yield {"type": "node_status", "node_id": parts[1], "status": parts[2]}
            elif line.startswith("NODE_LOG_JSON:"):
                try:
                    data = json.loads(line[len("NODE_LOG_JSON:"):])
                    yield {
                        "type": "node_log", 
                        "node_id": data.get("node_id"), 
                        "status": data.get("status"),
                        "input": data.get("input"),
                        "output": data.get("output"),
                        "duration": data.get("duration", 0)
                    }
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

# Singleton instance
deno_service = DenoService()
