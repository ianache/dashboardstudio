from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def _generate_id():
    import random
    return random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


@router.post("/", response_model=schemas.DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard: schemas.DashboardCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new dashboard (admin/designer only)"""
    db_dashboard = models.Dashboard(
        id=_generate_id(),
        name=dashboard.name,
        description=dashboard.description,
        is_public=dashboard.is_public,
        created_by=current_user.sub,
        filters=dashboard.filters or []
    )
    db.add(db_dashboard)
    db.commit()
    db.refresh(db_dashboard)
    return db_dashboard


@router.get("/", response_model=List[schemas.DashboardResponse])
async def list_dashboards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List dashboards based on user role"""
    if "admin" in current_user.roles or "designer" in current_user.roles:
        dashboards = db.query(models.Dashboard).offset(skip).limit(limit).all()
    else:
        # Viewers see public dashboards and their assigned ones
        dashboard_ids = [a.dashboard_id for a in db.query(models.DashboardAssignment).filter(models.DashboardAssignment.user_id == current_user.sub).all()]
        dashboards = db.query(models.Dashboard).filter(
            (models.Dashboard.is_public == True) | (models.Dashboard.id.in_(dashboard_ids))
        ).offset(skip).limit(limit).all()
    return dashboards


@router.get("/{dashboard_id}", response_model=schemas.DashboardWithAssignments)
async def get_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get dashboard by ID"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    # Check access
    if not dashboard.is_public:
        if "admin" in current_user.roles or "designer" in current_user.roles:
            pass
        else:
            assignment = db.query(models.DashboardAssignment).filter(
                models.DashboardAssignment.dashboard_id == dashboard_id,
                models.DashboardAssignment.user_id == current_user.sub
            ).first()
            if not assignment:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Get assigned users
    assignments = db.query(models.DashboardAssignment).filter(models.DashboardAssignment.dashboard_id == dashboard_id).all()
    assigned_users = [a.user_id for a in assignments]
    
    response = schemas.DashboardWithAssignments.model_validate(dashboard)
    response.assigned_users = assigned_users
    return response


@router.put("/{dashboard_id}", response_model=schemas.DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    dashboard_update: schemas.DashboardUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update dashboard (admin/designer only)"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    for key, value in dashboard_update.model_dump(exclude_unset=True).items():
        setattr(dashboard, key, value)
    
    db.commit()
    db.refresh(dashboard)
    return dashboard


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete dashboard (admin/designer only)"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    db.delete(dashboard)
    db.commit()
    return None


@router.post("/{dashboard_id}/assign", response_model=schemas.MessageResponse)
async def assign_dashboard(
    dashboard_id: str,
    assignment: schemas.DashboardAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Assign dashboard to users (admin/designer only)"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    # Remove existing assignments
    db.query(models.DashboardAssignment).filter(models.DashboardAssignment.dashboard_id == dashboard_id).delete()
    
    # Add new assignments
    for user_id in assignment.user_ids:
        assignment = models.DashboardAssignment(dashboard_id=dashboard_id, user_id=user_id)
        db.add(assignment)
    
    db.commit()
    return schemas.MessageResponse(message=f"Dashboard assigned to {len(assignment.user_ids)} users")


@router.delete("/{dashboard_id}/assign/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_dashboard(
    dashboard_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Remove user from dashboard assignment (admin/designer only)"""
    assignment = db.query(models.DashboardAssignment).filter(
        models.DashboardAssignment.dashboard_id == dashboard_id,
        models.DashboardAssignment.user_id == user_id
    ).first()
    
    if assignment:
        db.delete(assignment)
        db.commit()
    
    return None


@router.post("/{dashboard_id}/filters", response_model=schemas.DashboardResponse)
async def add_filter(
    dashboard_id: str,
    filter_data: dict,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Add filter to dashboard (admin/designer only)"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    filters = dashboard.filters or []
    filters.append({"id": _generate_id(), **filter_data})
    dashboard.filters = filters
    
    db.commit()
    db.refresh(dashboard)
    return dashboard


@router.delete("/{dashboard_id}/filters/{filter_id}", response_model=schemas.DashboardResponse)
async def remove_filter(
    dashboard_id: str,
    filter_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Remove filter from dashboard (admin/designer only)"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    if dashboard.filters:
        dashboard.filters = [f for f in dashboard.filters if f.get("id") != filter_id]
    
    db.commit()
    db.refresh(dashboard)
    return dashboard