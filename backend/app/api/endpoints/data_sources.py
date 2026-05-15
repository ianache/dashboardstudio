from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import random
import json

from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.core.encryption import process_sensitive_fields
from app.models import models

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


# ── Helpers: serialise connection_config into connection_url (DB compat) ───────
# The biportal.data_sources table was created without the connection_config
# column, so we persist the JSON config blob inside the existing connection_url
# VARCHAR(500) field and deserialise it transparently on read.

def _encode_config(config: dict) -> str:
    """Encrypt sensitive keys then JSON-serialise into connection_url."""
    encrypted = process_sensitive_fields(config or {}, action="encrypt")
    return json.dumps(encrypted)


def _decode_config(connection_url: str) -> dict:
    """Deserialise + decrypt connection_config stored in connection_url."""
    if not connection_url:
        return {}
    try:
        raw = json.loads(connection_url)
        return process_sensitive_fields(raw, action="decrypt")
    except Exception:
        # Stored value is a plain URL (legacy) — return as-is
        return {"url": connection_url}


# ── Inline schemas (the existing schemas.py uses the old connection_url field) ──

class DataSourceCreate(BaseModel):
    name: str
    type: str
    connection_config: Optional[dict] = {}
    description: Optional[str] = None
    status: Optional[str] = "active"
    is_active: bool = True


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    connection_config: Optional[dict] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    connection_config: Optional[dict] = {}
    description: Optional[str] = None
    is_active: bool
    status: Optional[str] = "active"
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def _gen_id():
    return "ds-" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=9))


def _to_response(ds: models.DataSource) -> dict:
    """Convert a DataSource ORM object to a response dict."""
    config = _decode_config(ds.connection_url or "")
    return {
        "id": ds.id,
        "name": ds.name,
        "type": ds.type,
        "connection_config": config,
        "description": ds.description,
        "is_active": ds.is_active,
        "status": "active" if ds.is_active else "inactive",
        "created_by": ds.created_by,
        "created_at": ds.created_at,
        "updated_at": ds.updated_at,
    }


# ── CRUD endpoints ─────────────────────────────────────────────────────────────

@router.get("/", response_model=List[DataSourceResponse])
async def list_data_sources(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """List all data sources."""
    await ensure_user_exists(current_user)
    rows = db.query(models.DataSource).order_by(models.DataSource.created_at.desc()).all()
    return [_to_response(ds) for ds in rows]


@router.post("/", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    payload: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"])),
):
    """Create a new data source."""
    await ensure_user_exists(current_user)
    ds = models.DataSource(
        id=_gen_id(),
        name=payload.name,
        type=payload.type,
        connection_url=_encode_config(payload.connection_config or {}),
        description=payload.description,
        is_active=payload.is_active,
        created_by=current_user.sub,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return _to_response(ds)


@router.get("/{id}", response_model=DataSourceResponse)
async def get_data_source(
    id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Get a single data source by ID."""
    ds = db.query(models.DataSource).filter(models.DataSource.id == id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    return _to_response(ds)


@router.put("/{id}", response_model=DataSourceResponse)
async def update_data_source(
    id: str,
    payload: DataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"])),
):
    """Update a data source."""
    ds = db.query(models.DataSource).filter(models.DataSource.id == id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "connection_config" in update_data and update_data["connection_config"] is not None:
        ds.connection_url = _encode_config(update_data.pop("connection_config"))
    if "status" in update_data:
        update_data["is_active"] = update_data.pop("status") == "active"

    for key, value in update_data.items():
        if hasattr(ds, key) and key not in ("connection_config",):
            setattr(ds, key, value)

    db.commit()
    db.refresh(ds)
    return _to_response(ds)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"])),
):
    """Delete a data source."""
    ds = db.query(models.DataSource).filter(models.DataSource.id == id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")
    db.delete(ds)
    db.commit()
    return None


@router.post("/{id}/test")
async def test_data_source(
    id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"])),
):
    """Test a data source connection."""
    ds = db.query(models.DataSource).filter(models.DataSource.id == id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")

    config = _decode_config(ds.connection_url or "")
    if not config:
        raise HTTPException(status_code=400, detail="No connection config found")

    # Inject the connection type from the ORM field so the strategy dispatcher can resolve it
    config["type"] = ds.type

    try:
        from app.services.connection_testing import connection_testing_service
        success = await connection_testing_service.test_connection(config)
        return {"success": success}
    except ImportError:
        return {"success": False, "message": "Connection testing service not available"}
    except Exception as e:
        return {"success": False, "message": str(e)}
