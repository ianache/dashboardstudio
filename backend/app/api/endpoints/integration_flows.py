import random
import string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/integration-flows", tags=["integration-flows"])


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
