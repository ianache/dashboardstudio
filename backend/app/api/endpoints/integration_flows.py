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
from app.services.scheduler import schedule_flow, unschedule_flow
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

        from app.services.source_executor import pre_execute_flow_nodes
        pre_exec_ok, flow_data = await pre_execute_flow_nodes(flow_data, db, websocket)

        if not pre_exec_ok:
            await websocket.send_json({"type": "status", "success": False, "exit_code": 1})
            return

        # Pre-create execution history record so that nested logs (like node_execution_logs)
        # can safely reference it without violating foreign key constraints.
        exec_id = 'exec-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        logger.info(f"Pre-creating execution history {exec_id} in database")
        try:
            execution = models.ExecutionHistory(
                id=exec_id,
                flow_id=flow_id,
                status="running",
                start_time=datetime.utcnow(),
                duration=0
            )
            db.add(execution)
            db.commit()
        except Exception as db_err:
            logger.error(f"Failed to pre-create execution history: {str(db_err)}")
            db.rollback()

        logger.info(f"WebSocket flow {flow_id}: Starting Deno stream")
        start_time = datetime.utcnow()
        all_logs = []
        node_logs = []
        final_result = None
        success = False

        log_count = 0
        async for log in deno_service.run_flow_stream(flow_data, payload, db=db, execution_id=exec_id):
            log_count += 1
            await websocket.send_json(log)
            
            if log["type"] == "status":
                success = log["success"]
            elif log["type"] == "result":
                final_result = log["data"]
            elif log["type"] == "node_log":
                node_logs.append(log)
            elif log["type"] in ["info", "error"]:
                all_logs.append(log)

        logger.info(f"WebSocket flow {flow_id}: Deno stream finished. Logs sent: {log_count}, success={success}")
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update execution history with final results
        try:
            logger.info(f"Updating execution {exec_id} in history")
            execution_record = db.query(models.ExecutionHistory).filter(models.ExecutionHistory.id == exec_id).first()
            if execution_record:
                execution_record.status = "success" if success else "error"
                execution_record.end_time = end_time
                execution_record.duration = duration_ms
            
            for nl in node_logs:
                start_dt = None
                if nl.get("start_time"):
                    try:
                        iso_str = nl.get("start_time").replace("Z", "+00:00")
                        start_dt = datetime.fromisoformat(iso_str)
                    except Exception:
                        pass
                
                end_dt = None
                if nl.get("end_time"):
                    try:
                        iso_str = nl.get("end_time").replace("Z", "+00:00")
                        end_dt = datetime.fromisoformat(iso_str)
                    except Exception:
                        pass

                db_nl = models.NodeExecutionLogs(
                    execution_id=exec_id,
                    node_id=nl.get("node_id"),
                    status=nl.get("status"),
                    input_data=nl.get("input"),
                    output_data=nl.get("output"),
                    error_message=nl.get("error_message"),
                    duration=nl.get("duration"),
                    start_time=start_dt or datetime.utcnow(),
                    end_time=end_dt
                )
                db.add(db_nl)
            
            # Update flow status
            flow.last_run = start_time
            flow.last_run_success = success
            db.commit()
            logger.info(f"Execution {exec_id} updated successfully")
        except Exception as db_err:
            logger.error(f"Failed to update execution history: {str(db_err)}")
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


@router.get("/{flow_id}/executions")
async def list_flow_executions(
    flow_id: str,
    limit: int = Query(20, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Lista las últimas ejecuciones de un flujo."""
    await ensure_user_exists(current_user)
    return db.query(models.ExecutionHistory)\
             .filter(models.ExecutionHistory.flow_id == flow_id)\
             .order_by(models.ExecutionHistory.start_time.desc())\
             .limit(limit).all()


@router.get("/executions/{exec_id}/logs")
async def get_execution_logs(
    exec_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Obtiene los logs y resultados de una ejecución específica."""
    await ensure_user_exists(current_user)
    execution = db.query(models.ExecutionHistory).filter(models.ExecutionHistory.id == exec_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    node_logs = db.query(models.NodeExecutionLogs).filter(models.NodeExecutionLogs.execution_id == exec_id).all()
    nl_dicts = [
        {
            "node_id": nl.node_id,
            "status": nl.status,
            "input": nl.input_data,
            "output": nl.output_data,
            "error_message": nl.error_message,
            "duration": nl.duration,
            "start_time": nl.start_time.isoformat() if nl.start_time else None,
            "end_time": nl.end_time.isoformat() if nl.end_time else None
        }
        for nl in node_logs
    ]
    
    return {
        "flow_id": execution.flow_id,
        "status": execution.status,
        "logs": nl_dicts,
        "result_data": None, 
        "duration_ms": execution.duration,
        "created_at": execution.start_time
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

    from app.services.source_executor import pre_execute_flow_nodes
    pre_exec_ok, flow_data = await pre_execute_flow_nodes(flow_data, db)

    start_time = datetime.utcnow()
    result = await deno_service.run_flow(flow_data, payload)
    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Save to history
    exec_id = 'exec-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    # Process logs to list of dicts
    all_logs = []
    node_logs = []
    if result.get("logs"):
        for line in result["logs"].split("\n"):
            line = line.strip()
            if line.startswith("NODE_LOG_JSON:"):
                try:
                    nl = json.loads(line[len("NODE_LOG_JSON:"):])
                    node_logs.append(nl)
                except:
                    pass
            elif not line.startswith("FINAL_RESULT:") and not line.startswith("NODE_STATUS:"):
                all_logs.append({"type": "info", "message": line})
    if result.get("errors"):
        for line in result["errors"].split("\n"):
            all_logs.append({"type": "error", "message": line})

    # Post-execute destination nodes
    from app.services.destination_executor import post_execute_flow_nodes
    node_logs = await post_execute_flow_nodes(flow_data, node_logs, db)

    execution = models.ExecutionHistory(
        id=exec_id,
        flow_id=flow_id,
        status=result["status"],
        start_time=start_time,
        end_time=datetime.utcnow(),
        duration=duration_ms
    )
    db.add(execution)
    
    for nl in node_logs:
        start_dt = None
        if nl.get("start_time"):
            try:
                iso_str = nl.get("start_time").replace("Z", "+00:00")
                start_dt = datetime.fromisoformat(iso_str)
            except Exception:
                pass
        
        end_dt = None
        if nl.get("end_time"):
            try:
                iso_str = nl.get("end_time").replace("Z", "+00:00")
                end_dt = datetime.fromisoformat(iso_str)
            except Exception:
                pass

        db_nl = models.NodeExecutionLogs(
            execution_id=exec_id,
            node_id=nl.get("node_id"),
            status=nl.get("status"),
            input_data=nl.get("input"),
            output_data=nl.get("output"),
            error_message=nl.get("error_message"),
            duration=nl.get("duration", 0),
            start_time=start_dt or datetime.utcnow(),
            end_time=end_dt
        )
        db.add(db_nl)
    
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
    flows = q.order_by(models.IntegrationFlow.created_at.desc()).all()
    
    # Compute dynamic progress and backfill missing last_run_success for older flows
    for flow in flows:
        latest_exec = db.query(models.ExecutionHistory).filter(models.ExecutionHistory.flow_id == flow.id).order_by(models.ExecutionHistory.start_time.desc()).first()
        if latest_exec:
            if latest_exec.status == "running":
                nodes_done = db.query(models.NodeExecutionLogs).filter(models.NodeExecutionLogs.execution_id == latest_exec.id).count()
                total = len(flow.flow_nodes) if flow.flow_nodes else 1
                prog = int((nodes_done / total) * 100)
                flow.progress = min(prog, 99) # 99% until fully success
            elif latest_exec.status == "success":
                flow.progress = 100
                flow.last_run_success = True
            else:
                flow.progress = 100
                flow.last_run_success = False
        else:
            flow.progress = 0
            
    return flows


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
    schedule_flow(flow)
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
    schedule_flow(flow)
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
    if "notes" in body:
        flow.flow_notes = body["notes"]
    if "metadata" in body:
        flow.flow_metadata = body["metadata"]
        # Sync top-level fields from metadata if present
        meta = body["metadata"]
        for field in ("name", "description", "status", "flow_type", "cron_expression", "log_level", "source_system", "target_system"):
            if field in meta:
                setattr(flow, field, meta[field])
    db.commit()
    db.refresh(flow)
    schedule_flow(flow)
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
    unschedule_flow(flow_id)
    return None
