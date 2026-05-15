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
        
    return execution
