from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from typing import List

router = APIRouter(prefix="/execution-history", tags=["execution-history"])

@router.get("/{flow_id}", response_model=List[schemas.ExecutionHistoryResponse])
async def get_execution_history(
    flow_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    history = db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.flow_id == flow_id
    ).order_by(models.ExecutionHistory.start_time.desc()).offset(offset).limit(limit).all()
    
    return history

@router.get("/detail/{execution_id}", response_model=schemas.ExecutionDetailResponse)
async def get_execution_detail(
    execution_id: str,
    db: Session = Depends(get_db)
):
    execution = db.query(models.ExecutionHistory).filter(
        models.ExecutionHistory.id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    # Build tools and nodes lookup to construct rich titles
    tools = db.query(models.EditorTool).all()
    tool_type_names = {t.type: t.name for t in tools}
    
    nodes_lookup = {}
    if execution.flow:
        nodes_lookup = {node["id"]: node for node in (execution.flow.flow_nodes or [])}
        
    node_logs = []
    for log in execution.node_logs:
        node_info = nodes_lookup.get(log.node_id, {})
        tool_type = node_info.get("toolType", "")
        type_name = tool_type_names.get(tool_type, tool_type.replace("_", " ").title() if tool_type else "Sistema")
        node_name = node_info.get("label") or node_info.get("name") or type_name
        node_title = f"{type_name} ({node_name}): {log.node_id}"
        
        node_logs.append({
            "node_id": log.node_id,
            "node_title": node_title,
            "status": log.status,
            "start_time": log.start_time,
            "end_time": log.end_time,
            "duration": log.duration,
            "input_data": log.input_data,
            "output_data": log.output_data
        })
        
    return {
        "id": execution.id,
        "flow_id": execution.flow_id,
        "status": execution.status,
        "start_time": execution.start_time,
        "end_time": execution.end_time,
        "duration": execution.duration,
        "node_logs": node_logs
    }
