from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
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
    # Ensure user exists in database
    await ensure_user_exists(current_user)
    
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
    
    # Initialize assigned_users as empty list for response
    db_dashboard.assigned_users = []
    return db_dashboard


@router.get("/", response_model=List[schemas.DashboardResponse])
async def list_dashboards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List dashboards based on user role"""
    query = db.query(models.Dashboard).options(joinedload(models.Dashboard.assignments))
    
    if "admin" in current_user.roles or "designer" in current_user.roles:
        dashboards = query.offset(skip).limit(limit).all()
    else:
        # Viewers see public dashboards and their assigned ones
        dashboard_ids = [a.dashboard_id for a in db.query(models.DashboardAssignment).filter(models.DashboardAssignment.user_id == current_user.sub).all()]
        dashboards = query.filter(
            (models.Dashboard.is_public == True) | (models.Dashboard.id.in_(dashboard_ids))
        ).offset(skip).limit(limit).all()
        
    # Map assignments to assigned_users list for Pydantic
    for d in dashboards:
        d.assigned_users = [a.user_id for a in d.assignments]
        
    return dashboards


@router.get("/{dashboard_id}", response_model=schemas.DashboardWithAssignments)
async def get_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get dashboard by ID"""
    dashboard = db.query(models.Dashboard).options(joinedload(models.Dashboard.assignments)).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    # Check access
    if not dashboard.is_public:
        if "admin" in current_user.roles or "designer" in current_user.roles:
            pass
        else:
            assignment = next((a for a in dashboard.assignments if a.user_id == current_user.sub), None)
            if not assignment:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Map assignments to assigned_users list
    dashboard.assigned_users = [a.user_id for a in dashboard.assignments]
    
    return dashboard


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
    assignment_data: schemas.DashboardAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Assign dashboard to users (admin/designer only)"""
    dashboard = db.query(models.Dashboard).filter(models.Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    
    # Validate that all target users exist in the database
    if assignment_data.user_ids:
        existing_users = db.query(models.User.id).filter(
            models.User.id.in_(assignment_data.user_ids)
        ).all()
        existing_ids = {row.id for row in existing_users}
        missing_ids = [uid for uid in assignment_data.user_ids if uid not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following user IDs are not registered in the system: {missing_ids}. "
                       "Users must log in at least once before being assigned to a dashboard."
            )

    # Remove existing assignments
    db.query(models.DashboardAssignment).filter(models.DashboardAssignment.dashboard_id == dashboard_id).delete()
    
    # Add new assignments
    for user_id in assignment_data.user_ids:
        new_assignment = models.DashboardAssignment(dashboard_id=dashboard_id, user_id=user_id)
        db.add(new_assignment)
    
    db.commit()
    return schemas.MessageResponse(message=f"Dashboard assigned to {len(assignment_data.user_ids)} users")


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
    
    dashboard.filters = [*(dashboard.filters or []), {"id": _generate_id(), **filter_data}]
    
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