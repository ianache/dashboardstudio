from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/dashboards/{dashboard_id}/widgets", tags=["widgets"])


def _generate_id():
    import random
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


@router.post("/", response_model=schemas.WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: str,
    widget: schemas.WidgetCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new widget in a dashboard (admin/designer only)"""
    # Ensure user exists in database
    await ensure_user_exists(current_user)
    
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    db_widget = models.Widget(
        id=_generate_id(),
        dashboard_id=dashboard_id,
        title=widget.title,
        chart_type=widget.chart_type,
        position_x=widget.position.x,
        position_y=widget.position.y,
        position_w=widget.position.w,
        position_h=widget.position.h,
        cube_query=widget.cube_query.model_dump(),
        chart_options=widget.chart_options,
        use_mock_data=widget.use_mock_data
    )
    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)
    return db_widget


@router.get("/", response_model=List[schemas.WidgetResponse])
async def list_widgets(
    dashboard_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all widgets in a dashboard"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    widgets = db.query(models.Widget).filter(models.Widget.dashboard_id == dashboard_id).all()
    return widgets


@router.get("/{widget_id}", response_model=schemas.WidgetResponse)
async def get_widget(
    dashboard_id: str,
    widget_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get widget by ID"""
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.dashboard_id == dashboard_id
    ).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    return widget


@router.put("/{widget_id}", response_model=schemas.WidgetResponse)
async def update_widget(
    dashboard_id: str,
    widget_id: str,
    widget_update: schemas.WidgetUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update widget (admin/designer only)"""
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.dashboard_id == dashboard_id
    ).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    
    update_data = widget_update.model_dump(exclude_unset=True)
    
    if "position" in update_data:
        pos = update_data.pop("position") or {}
        widget.position_x = int(pos["x"]) if pos.get("x") is not None else widget.position_x
        widget.position_y = int(pos["y"]) if pos.get("y") is not None else widget.position_y
        widget.position_w = int(pos["w"]) if pos.get("w") is not None else widget.position_w
        widget.position_h = int(pos["h"]) if pos.get("h") is not None else widget.position_h
    
    for key, value in update_data.items():
        setattr(widget, key, value)
    
    db.commit()
    db.refresh(widget)
    return widget


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    dashboard_id: str,
    widget_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete widget (admin/designer only)"""
    widget = db.query(models.Widget).filter(
        models.Widget.id == widget_id,
        models.Widget.dashboard_id == dashboard_id
    ).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")
    
    db.delete(widget)
    db.commit()
    return None