import asyncio
import random
import string
import logging
import traceback
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

from app.services.deno_service import deno_service
from app.services.source_executor import execute_source_node, POSTGRES_TYPES, MYSQL_TYPES, HTTP_TYPES
from app.api.endpoints.data_sources import _decode_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integration-flows", tags=["integration-flows"])


@router.websocket("/{flow_id}/logs")
async def flow_logs_websocket(websocket: WebSocket, flow_id: str, db: Session = Depends(get_db)):
    """Streaming de logs de ejecución vía WebSocket."""
    logger.info(f"WebSocket connection attempt for flow: {flow_id}")
    await websocket.accept()
    
    flow = db.query(models.IntegrationFlow).filter(models.IntegrationFlow.id == flow_id).first()
    if not flow:
        logger.warning(f"Flow {flow_id} not found for WebSocket")
        await websocket.send_json({"type": "error", "message": "Flow not found"})
        await websocket.close()
        return

    try:
        logger.info(f"WebSocket flow {flow_id}: Waiting for initial message")
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"WebSocket flow {flow_id}: Timeout waiting for initial message")
            await websocket.send_json({"type": "error", "message": "Timeout waiting for client payload"})
            await websocket.close()
            return

        logger.info(f"WebSocket flow {flow_id}: Received initial message: {data}")
        payload = data.get("payload", {})
        user_id = data.get("user_id")

        if not flow.flow_nodes:
            logger.warning(f"WebSocket flow {flow_id}: Flow has no nodes")
            await websocket.send_json({"type": "error", "message": "El flujo no tiene nodos para ejecutar"})
            await websocket.close()
            return

        flow_data = {
            "nodes": flow.flow_nodes,
            "connections": flow.flow_connections,
            "metadata": flow.flow_metadata
        }

        # ── Pre-execute source nodes in Python (before Deno) ──────────────────
        # Deno runs with --no-remote (no network), so Python resolves source nodes
        # (DB queries, REST calls) first and injects results as initial payload.
        import json as _json
        from copy import deepcopy

        RESOLVABLE = POSTGRES_TYPES | MYSQL_TYPES | HTTP_TYPES
        nodes_copy  = deepcopy(flow.flow_nodes or [])
        initial_payload = payload or {}
        prefetched_outputs = {}
        pre_exec_ok = True

        for node in nodes_copy:
            if node.get("category") != "source":
                continue
            conn_type = (node.get("props") or {}).get("connection_type", "").lower()
            if conn_type not in RESOLVABLE:
                continue  # let Deno handle unknown source types

            # Emit running status immediately
            await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "running"})
            await websocket.send_json({"type": "info",
                "message": f"[Fuente] Ejecutando '{node.get('label', node['id'])}' ..."})

            # ── Enrich node props with credentials from DB (decrypted) ──────────────
            # The frontend auto-fill only copies keys that already exist in prop_defs,
            # so username/password may be missing. We resolve them server-side from
            # the DataSource record to guarantee correct credentials.
            connection_id = (node.get("props") or {}).get("connection_id", "")
            if connection_id:
                ds = db.query(models.DataSource).filter(models.DataSource.id == connection_id).first()
                if ds:
                    resolved_cfg = _decode_config(ds.connection_url or "")
                    if not node.get("props"):
                        node["props"] = {}
                    # Merge: DB credentials always take precedence over node.props values
                    for cfg_key in ["host", "port", "username", "password", "database",
                                    "schema", "url", "email", "api_key", "token",
                                    "token_url", "client_id", "client_secret"]:
                        if cfg_key in resolved_cfg:
                            node["props"][cfg_key] = resolved_cfg[cfg_key]
                    # Also ensure connection_type matches what's stored in the DataSource
                    if ds.type:
                        node["props"]["connection_type"] = ds.type
                    logger.info(f"[SourceExec] Credenciales resueltas desde DataSource '{ds.name}' "
                                f"(user={resolved_cfg.get('username', '<vacío>')})")
                else:
                    logger.warning(f"[SourceExec] DataSource '{connection_id}' no encontrado en DB")
            # ───────────────────────────────────────────────────────────────────────

            result = await execute_source_node(node)

            if result["success"]:
                prefetched_outputs[node["id"]] = result["rows"]
                node["__pre_executed"] = True
                await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "success"})
                await websocket.send_json({"type": "info",
                    "message": f"[Fuente] {result['count']} registros cargados desde '{node.get('label', '')}'"})
            else:
                node["__pre_executed"] = True  # skip in Deno so error is the final state
                await websocket.send_json({"type": "node_status", "node_id": node["id"], "status": "error"})
                await websocket.send_json({"type": "error",
                    "message": f"[Fuente Error] {result['error']}"})
                pre_exec_ok = False
                break  # abort further execution on source failure

        if not pre_exec_ok:
            await websocket.send_json({"type": "status", "success": False, "exit_code": 1})
            return

        # Replace nodes list with annotated copy so runner.ts can skip pre-executed nodes
        flow_data["nodes"] = nodes_copy
        flow_data["prefetched_outputs"] = prefetched_outputs

        logger.info(f"WebSocket flow {flow_id}: Starting Deno stream")
        start_time = datetime.utcnow()
        all_logs = []
        final_result = None
        success = False

        log_count = 0
        async for log in deno_service.run_flow_stream(flow_data, initial_payload):
            log_count += 1
            await websocket.send_json(log)
            
            if log["type"] == "status":
                success = log["success"]
            elif log["type"] == "result":
                final_result = log["data"]
            elif log["type"] in ["info", "error"]:
                all_logs.append(log)

        logger.info(f"WebSocket flow {flow_id}: Deno stream finished. Logs sent: {log_count}, success={success}")
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Save to history
        try:
            exec_id = 'exec-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            logger.info(f"Saving execution {exec_id} to history")
            
            execution = models.IntegrationFlowExecution(
                id=exec_id,
                flow_id=flow_id,
                status="success" if success else "error",
                logs=all_logs,
                result_data=final_result,
                duration_ms=duration_ms,
                executed_by=user_id,
                created_at=start_time
            )
            db.add(execution)
            
            # Update flow status
            flow.last_run = start_time
            flow.last_run_success = success
            db.commit()
            logger.info(f"Execution {exec_id} saved successfully")
        except Exception as db_err:
            logger.error(f"Failed to save execution history: {str(db_err)}")
            # Don't fail the WebSocket if only DB history fails
            db.rollback()

        # Small delay so the browser can process the final 'status' message
        # before the TCP close frame arrives (prevents false "unexpected close")
        await asyncio.sleep(0.15)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for flow {flow_id}")
    except Exception as e:
        logger.error(f"Error in flow_logs_websocket for {flow_id}: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            await websocket.send_json({"type": "error", "message": f"Server Error: {str(e)}"})
        except:
            pass
    finally:
        logger.info(f"Closing WebSocket for flow {flow_id}")
        try:
            await websocket.close()
        except:
            pass


@router.get("/{flow_id}/executions", response_model=List[schemas.IntegrationFlowExecutionResponse])
async def list_flow_executions(
    flow_id: str,
    limit: int = Query(20, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Lista las últimas ejecuciones de un flujo."""
    await ensure_user_exists(current_user)
    return db.query(models.IntegrationFlowExecution)\
             .filter(models.IntegrationFlowExecution.flow_id == flow_id)\
             .order_by(models.IntegrationFlowExecution.created_at.desc())\
             .limit(limit).all()


@router.get("/executions/{exec_id}/logs")
async def get_execution_logs(
    exec_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Obtiene los logs y resultados de una ejecución específica."""
    await ensure_user_exists(current_user)
    execution = db.query(models.IntegrationFlowExecution).filter(models.IntegrationFlowExecution.id == exec_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "status": execution.status,
        "logs": execution.logs,
        "result_data": execution.result_data,
        "duration_ms": execution.duration_ms,
        "created_at": execution.created_at
    }


@router.post("/check-runtime")
async def check_deno_runtime(
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Verifica el estado del runtime de Deno y realiza una ejecución de prueba."""
    status = await deno_service.check_runtime()
    
    test_script = "return { message: 'Hello from Deno!', timestamp: new Date().toISOString() };"
    test_run = await deno_service.run_flow_test(test_script)
    
    return {
        "runtime": status,
        "test_execution": test_run
    }


@router.post("/{flow_id}/run")
async def run_integration_flow(
    flow_id: str,
    payload: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Ejecuta un flujo de integración en el runtime de Deno."""
    flow = db.query(models.IntegrationFlow).filter(models.IntegrationFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration flow not found")

    flow_data = {
        "nodes": flow.flow_nodes,
        "connections": flow.flow_connections,
        "metadata": flow.flow_metadata
    }

    start_time = datetime.utcnow()
    result = await deno_service.run_flow(flow_data, payload)
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Save to history
    exec_id = 'exec-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    # Process logs to list of dicts
    all_logs = []
    if result.get("logs"):
        for line in result["logs"].split("\n"):
            if not line.startswith("FINAL_RESULT:"):
                all_logs.append({"type": "info", "message": line})
    if result.get("errors"):
        for line in result["errors"].split("\n"):
            all_logs.append({"type": "error", "message": line})

    execution = models.IntegrationFlowExecution(
        id=exec_id,
        flow_id=flow_id,
        status=result["status"],
        logs=all_logs,
        result_data=result.get("result"),
        duration_ms=duration_ms,
        executed_by=current_user.user_id,
        created_at=start_time
    )
    db.add(execution)
    
    # Update flow status in DB
    flow.last_run = start_time
    flow.last_run_success = (result["status"] == "success")
    db.commit()

    return result


def _gen_id():
    return 'flow-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))


@router.get("/", response_model=List[schemas.IntegrationFlowResponse])
async def list_integration_flows(
    status: Optional[str] = Query(None),
    diagram_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await ensure_user_exists(current_user)
    q = db.query(models.IntegrationFlow)
    if status:
        q = q.filter(models.IntegrationFlow.status == status)
    if diagram_type:
        q = q.filter(models.IntegrationFlow.diagram_type == diagram_type)
    return q.order_by(models.IntegrationFlow.created_at.desc()).all()


@router.get("/{flow_id}", response_model=schemas.IntegrationFlowResponse)
async def get_integration_flow(
    flow_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    flow = db.query(models.IntegrationFlow).filter(models.IntegrationFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration flow not found")
    return flow


@router.post("/", response_model=schemas.IntegrationFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_integration_flow(
    body: schemas.IntegrationFlowCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    await ensure_user_exists(current_user)
    flow = models.IntegrationFlow(
        id=_gen_id(),
        created_by=current_user.sub,
        **body.model_dump()
    )
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


@router.put("/{flow_id}", response_model=schemas.IntegrationFlowResponse)
async def update_integration_flow(
    flow_id: str,
    body: schemas.IntegrationFlowUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    flow = db.query(models.IntegrationFlow).filter(models.IntegrationFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration flow not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(flow, key, value)
    db.commit()
    db.refresh(flow)
    return flow


@router.put("/{flow_id}/diagram", response_model=schemas.IntegrationFlowResponse)
async def save_flow_diagram(
    flow_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Save diagram data (nodes + connections + metadata) for a flow."""
    flow = db.query(models.IntegrationFlow).filter(models.IntegrationFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration flow not found")
    if "nodes" in body:
        flow.flow_nodes = body["nodes"]
    if "connections" in body:
        flow.flow_connections = body["connections"]
    if "metadata" in body:
        flow.flow_metadata = body["metadata"]
        # Sync top-level fields from metadata if present
        meta = body["metadata"]
        for field in ("name", "description", "status", "flow_type", "schedule", "source_system", "target_system"):
            if field in meta:
                setattr(flow, field, meta[field])
    db.commit()
    db.refresh(flow)
    return flow


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration_flow(
    flow_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    flow = db.query(models.IntegrationFlow).filter(models.IntegrationFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration flow not found")
    db.delete(flow)
    db.commit()
    return None
