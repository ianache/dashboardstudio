from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/cube-config", tags=["cube-config"])


def _generate_id():
    import random
    return 'cube-' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


@router.post("/", response_model=schemas.CubeConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_cube_config(
    config: schemas.CubeConfigCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create CubeJS configuration (admin/designer only)"""
    db_config = models.CubeConfig(
        id=_generate_id(),
        name=config.name,
        api_url=config.api_url,
        api_token=config.api_token,
        is_active=config.is_active,
        created_by=current_user.sub
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/", response_model=List[schemas.CubeConfigResponse])
async def list_cube_configs(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all CubeJS configurations"""
    configs = db.query(models.CubeConfig).all()
    return configs


@router.get("/active", response_model=schemas.CubeConfigResponse)
async def get_active_cube_config(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get active CubeJS configuration"""
    config = db.query(models.CubeConfig).filter(models.CubeConfig.is_active == True).first()
    if not config:
        # Return demo config
        return schemas.CubeConfigResponse(
            id="demo",
            name="Demo",
            api_url="http://localhost:4000/cubejs-api/v1",
            api_token="",
            is_active=True,
            created_by=None,
            created_at=None,
            updated_at=None
        )
    return config


@router.get("/{config_id}", response_model=schemas.CubeConfigResponse)
async def get_cube_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get CubeJS configuration by ID"""
    config = db.query(models.CubeConfig).filter(models.CubeConfig.id == config_id).first()
    if not config:
        if config_id == "demo":
            return schemas.CubeConfigResponse(
                id="demo",
                name="Demo",
                api_url="http://localhost:4000/cubejs-api/v1",
                api_token="",
                is_active=True,
                created_by=None,
                created_at=None,
                updated_at=None
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    return config


@router.put("/{config_id}", response_model=schemas.CubeConfigResponse)
async def update_cube_config(
    config_id: str,
    config_update: schemas.CubeConfigUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update CubeJS configuration (admin/designer only)"""
    config = db.query(models.CubeConfig).filter(models.CubeConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    
    for key, value in config_update.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cube_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete CubeJS configuration (admin/designer only)"""
    config = db.query(models.CubeConfig).filter(models.CubeConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    
    db.delete(config)
    db.commit()
    return None


@router.post("/{config_id}/activate", response_model=schemas.CubeConfigResponse)
async def activate_cube_config(
    config_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Activate a CubeJS configuration (admin/designer only)"""
    config = db.query(models.CubeConfig).filter(models.CubeConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    
    db.query(models.CubeConfig).update({models.CubeConfig.is_active: False})
    config.is_active = True
    
    db.commit()
    db.refresh(config)
    return config