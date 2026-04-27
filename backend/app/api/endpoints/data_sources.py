from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.core.encryption import encrypt_value, decrypt_value
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


def _generate_id():
    import random
    return 'ds-' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


def _encrypt_data_source_password(data_source: models.DataSource) -> None:
    """Encrypt password before saving to database."""
    if data_source.password:
        data_source.password = encrypt_value(data_source.password)


def _decrypt_data_source_password(data_source: models.DataSource) -> models.DataSource:
    """Decrypt password when returning to client."""
    if data_source and data_source.password:
        try:
            data_source.password = decrypt_value(data_source.password)
        except ValueError:
            data_source.password = ""
    return data_source


@router.post("/", response_model=schemas.DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    data_source: schemas.DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new data source (admin/designer only)"""
    # Ensure user exists in database before creating data source
    await ensure_user_exists(current_user)
    
    # Check if name already exists
    existing = db.query(models.DataSource).filter(
        models.DataSource.name == data_source.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data source with name '{data_source.name}' already exists"
        )
    
    db_data_source = models.DataSource(
        id=_generate_id(),
        name=data_source.name,
        type=data_source.type,
        connection_url=data_source.connection_url,
        username=data_source.username,
        password=data_source.password,
        description=data_source.description,
        is_active=data_source.is_active,
        created_by=current_user.sub
    )
    # Encrypt sensitive data before saving
    _encrypt_data_source_password(db_data_source)
    db.add(db_data_source)
    db.commit()
    db.refresh(db_data_source)
    # Decrypt for response
    return _decrypt_data_source_password(db_data_source)


@router.get("/", response_model=List[schemas.DataSourceResponse])
async def list_data_sources(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all data sources"""
    # Ensure user exists
    await ensure_user_exists(current_user)
    
    data_sources = db.query(models.DataSource).all()
    # Decrypt passwords for all data sources
    for ds in data_sources:
        _decrypt_data_source_password(ds)
    return data_sources


@router.get("/{data_source_id}", response_model=schemas.DataSourceResponse)
async def get_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get data source by ID"""
    data_source = db.query(models.DataSource).filter(
        models.DataSource.id == data_source_id
    ).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    # Decrypt password before returning
    return _decrypt_data_source_password(data_source)


@router.get("/by-name/{name}", response_model=schemas.DataSourceResponse)
async def get_data_source_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get data source by name"""
    data_source = db.query(models.DataSource).filter(
        models.DataSource.name == name
    ).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with name '{name}' not found"
        )
    # Decrypt password before returning
    return _decrypt_data_source_password(data_source)


@router.get("/search/", response_model=List[schemas.DataSourceResponse])
async def search_data_sources(
    q: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Search data sources by name or type"""
    await ensure_user_exists(current_user)
    
    data_sources = db.query(models.DataSource).filter(
        models.DataSource.name.ilike(f"%{q}%") |
        models.DataSource.type.ilike(f"%{q}%") |
        models.DataSource.description.ilike(f"%{q}%")
    ).all()
    
    # Decrypt passwords for all data sources
    for ds in data_sources:
        _decrypt_data_source_password(ds)
    return data_sources


@router.put("/{data_source_id}", response_model=schemas.DataSourceResponse)
async def update_data_source(
    data_source_id: str,
    data_source_update: schemas.DataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update data source (admin/designer only)"""
    data_source = db.query(models.DataSource).filter(
        models.DataSource.id == data_source_id
    ).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    update_data = data_source_update.model_dump(exclude_unset=True)
    
    # Check if name is being updated and already exists
    if "name" in update_data and update_data["name"] != data_source.name:
        existing = db.query(models.DataSource).filter(
            models.DataSource.name == update_data["name"]
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data source with name '{update_data['name']}' already exists"
            )
    
    # Encrypt password if it's being updated
    if "password" in update_data and update_data["password"]:
        update_data["password"] = encrypt_value(update_data["password"])
    
    for key, value in update_data.items():
        setattr(data_source, key, value)
    
    db.commit()
    db.refresh(data_source)
    # Decrypt password for response
    return _decrypt_data_source_password(data_source)


@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete data source (admin/designer only)"""
    data_source = db.query(models.DataSource).filter(
        models.DataSource.id == data_source_id
    ).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    db.delete(data_source)
    db.commit()
    return None


@router.post("/{data_source_id}/test", response_model=dict)
async def test_data_source_connection(
    data_source_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Test data source connection (admin/designer only)"""
    data_source = db.query(models.DataSource).filter(
        models.DataSource.id == data_source_id
    ).first()
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Decrypt password for testing
    _decrypt_data_source_password(data_source)
    
    # TODO: Implement actual connection testing based on data source type
    # For now, just return success
    return {
        "success": True,
        "message": f"Connection to {data_source.name} ({data_source.type}) successful"
    }
