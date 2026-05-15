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


from app.core.encryption import process_sensitive_fields
from app.services.connection_testing import connection_testing_service

@router.post("/{id}/test")
async def test_data_source(
    id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Test a data source connection"""
    db_ds = db.query(models.DataSource).filter(models.DataSource.id == id).first()
    if not db_ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    if not db_ds.connection_config:
        raise HTTPException(status_code=400, detail="No connection config found")
        
    # Decrypt config recursively
    config = process_sensitive_fields(db_ds.connection_config, action="decrypt")
    
    try:
        success = await connection_testing_service.test_connection(config)
        return {"success": success}
    except Exception as e:
        return {"success": False, "message": str(e)}
