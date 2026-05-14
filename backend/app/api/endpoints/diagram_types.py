from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/diagram-types", tags=["diagram-types"])


@router.get("/", response_model=List[schemas.DiagramTypeResponse])
async def list_diagram_types(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await ensure_user_exists(current_user)
    return db.query(models.DiagramType).order_by(models.DiagramType.name).all()


@router.get("/{type_id}", response_model=schemas.DiagramTypeResponse)
async def get_diagram_type(
    type_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    dt = db.query(models.DiagramType).filter(models.DiagramType.id == type_id).first()
    if not dt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagram type not found")
    return dt


@router.post("/", response_model=schemas.DiagramTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram_type(
    body: schemas.DiagramTypeCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    await ensure_user_exists(current_user)
    if db.query(models.DiagramType).filter(models.DiagramType.id == body.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Diagram type '{body.id}' already exists")
    dt = models.DiagramType(**body.model_dump())
    db.add(dt)
    db.commit()
    db.refresh(dt)
    return dt


@router.put("/{type_id}", response_model=schemas.DiagramTypeResponse)
async def update_diagram_type(
    type_id: str,
    body: schemas.DiagramTypeUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    dt = db.query(models.DiagramType).filter(models.DiagramType.id == type_id).first()
    if not dt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagram type not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(dt, key, value)
    db.commit()
    db.refresh(dt)
    return dt


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram_type(
    type_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    dt = db.query(models.DiagramType).filter(models.DiagramType.id == type_id).first()
    if not dt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagram type not found")
    db.delete(dt)
    db.commit()
    return None
