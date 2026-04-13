from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/dimensional-models", tags=["dimensional-models"])


def _generate_id():
    import random
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


@router.post("/", response_model=schemas.DimensionalModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model: schemas.DimensionalModelCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new dimensional model (admin/designer only)"""
    # Ensure user exists in database
    await ensure_user_exists(current_user)
    
    if model.is_global:
        # Only one global model allowed
        db.query(models.DimensionalModel).filter(models.DimensionalModel.is_global == True).update({"is_global": False})
    
    db_model = models.DimensionalModel(
        id=_generate_id(),
        name=model.name,
        description=model.description,
        is_global=model.is_global,
        created_by=current_user.sub,
        nodes=model.nodes or [],
        relationships=model.relationships or []
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


@router.get("/", response_model=List[schemas.DimensionalModelResponse])
async def list_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all dimensional models"""
    models_list = db.query(models.DimensionalModel).offset(skip).limit(limit).all()
    
    # Ensure global model exists
    if not any(m.is_global for m in models_list):
        global_model = models.DimensionalModel(
            id="global-default",
            name="Global",
            description="Dimensiones compartidas entre todos los modelos dimensionales",
            is_global=True,
            created_by="system",
            nodes=[],
            relationships=[]
        )
        db.add(global_model)
        db.commit()
        models_list = db.query(models.DimensionalModel).offset(skip).limit(limit).all()
    
    return models_list


@router.get("/{model_id}", response_model=schemas.DimensionalModelResponse)
async def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get dimensional model by ID"""
    model = db.query(models.DimensionalModel).filter(models.DimensionalModel.id == model_id).first()
    if not model:
        if model_id == "global-default":
            return schemas.DimensionalModelResponse(
                id="global-default",
                name="Global",
                description="Dimensiones compartidas entre todos los modelos dimensionales",
                is_global=True,
                nodes=[],
                relationships=[],
                created_by="system",
                created_at=None,
                updated_at=None
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=schemas.DimensionalModelResponse)
async def update_model(
    model_id: str,
    model_update: schemas.DimensionalModelUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update dimensional model (admin/designer only)"""
    model = db.query(models.DimensionalModel).filter(models.DimensionalModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    update_data = model_update.model_dump(exclude_unset=True)
    
    if update_data.get("is_global") and model.is_global != True:
        db.query(models.DimensionalModel).filter(
            models.DimensionalModel.is_global == True,
            models.DimensionalModel.id != model_id
        ).update({"is_global": False})
    
    for key, value in update_data.items():
        setattr(model, key, value)
    
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete dimensional model (admin/designer only)"""
    model = db.query(models.DimensionalModel).filter(models.DimensionalModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    if model.is_global:
        raise HTTPException(status_code=status.HTTP_400_FORBIDDEN, detail="Cannot delete global model")
    
    db.delete(model)
    db.commit()
    return None


@router.post("/{model_id}/global", response_model=schemas.DimensionalModelResponse)
async def set_global_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Set model as global (admin/designer only)"""
    model = db.query(models.DimensionalModel).filter(models.DimensionalModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    db.query(models.DimensionalModel).filter(models.DimensionalModel.is_global == True).update({"is_global": False})
    model.is_global = True
    
    db.commit()
    db.refresh(model)
    return model