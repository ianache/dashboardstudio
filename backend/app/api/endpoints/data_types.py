from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/data-types", tags=["data-types"])


def _generate_id():
    import random
    return 'dt-' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


DEFAULT_TYPES = [
    {"name": "Serial", "base_type": "SERIAL", "size": None, "precision": None, "description": "Entero autoincremental (clave primaria)"},
    {"name": "Entero", "base_type": "INTEGER", "size": None, "precision": None, "description": "Número entero de 32 bits"},
    {"name": "Entero grande", "base_type": "BIGINT", "size": None, "precision": None, "description": "Número entero de 64 bits"},
    {"name": "Decimal", "base_type": "NUMERIC", "size": 18, "precision": 4, "description": "Número decimal de alta precisión"},
    {"name": "Moneda", "base_type": "NUMERIC", "size": 18, "precision": 2, "description": "Valores monetarios"},
    {"name": "Porcentaje", "base_type": "NUMERIC", "size": 5, "precision": 2, "description": "Valores porcentuales (0-100)"},
    {"name": "Texto", "base_type": "VARCHAR", "size": 255, "precision": None, "description": "Cadena de texto variable"},
    {"name": "Texto largo", "base_type": "TEXT", "size": None, "precision": None, "description": "Texto sin límite de longitud"},
    {"name": "Booleano", "base_type": "BOOLEAN", "size": None, "precision": None, "description": "Verdadero / Falso"},
    {"name": "Fecha", "base_type": "DATE", "size": None, "precision": None, "description": "Fecha sin hora (YYYY-MM-DD)"},
    {"name": "Timestamp", "base_type": "TIMESTAMP", "size": None, "precision": None, "description": "Fecha y hora sin zona horaria"},
    {"name": "Timestamp TZ", "base_type": "TIMESTAMPTZ", "size": None, "precision": None, "description": "Fecha y hora con zona horaria"},
    {"name": "UUID", "base_type": "UUID", "size": None, "precision": None, "description": "Identificador único universal"},
    {"name": "JSONB", "base_type": "JSONB", "size": None, "precision": None, "description": "Documento JSON binario indexable"},
]


@router.get("/", response_model=List[schemas.DataTypeResponse])
async def list_data_types(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all data types"""
    types = db.query(models.DataType).all()
    
    if not types:
        return [
            schemas.DataTypeResponse(id=f"dt-default-{i}", **dt, is_builtin=True, created_at=None, updated_at=None)
            for i, dt in enumerate(DEFAULT_TYPES)
        ]
    
    return types


@router.get("/{data_type_id}", response_model=schemas.DataTypeResponse)
async def get_data_type(
    data_type_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get data type by ID"""
    dt = db.query(models.DataType).filter(models.DataType.id == data_type_id).first()
    if not dt:
        # Check defaults
        for i, default in enumerate(DEFAULT_TYPES):
            if f"dt-default-{i}" == data_type_id:
                return schemas.DataTypeResponse(id=data_type_id, **default, is_builtin=True, created_at=None, updated_at=None)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data type not found")
    return dt


@router.post("/", response_model=schemas.DataTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_data_type(
    data_type: schemas.DataTypeCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new data type (admin/designer only)"""
    db_type = models.DataType(
        id=_generate_id(),
        name=data_type.name,
        base_type=data_type.base_type,
        size=data_type.size,
        precision=data_type.precision,
        description=data_type.description,
        is_builtin=False
    )
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type


@router.put("/{data_type_id}", response_model=schemas.DataTypeResponse)
async def update_data_type(
    data_type_id: str,
    data_type_update: schemas.DataTypeUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update data type (admin/designer only)"""
    dt = db.query(models.DataType).filter(models.DataType.id == data_type_id).first()
    if not dt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data type not found")
    
    if dt.is_builtin:
        raise HTTPException(status_code=status.HTTP_400_FORBIDDEN, detail="Cannot modify built-in data types")
    
    for key, value in data_type_update.model_dump(exclude_unset=True).items():
        setattr(dt, key, value)
    
    db.commit()
    db.refresh(dt)
    return dt


@router.delete("/{data_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_type(
    data_type_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete data type (admin/designer only)"""
    dt = db.query(models.DataType).filter(models.DataType.id == data_type_id).first()
    if not dt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data type not found")
    
    if dt.is_builtin:
        raise HTTPException(status_code=status.HTTP_400_FORBIDDEN, detail="Cannot delete built-in data types")
    
    db.delete(dt)
    db.commit()
    return None