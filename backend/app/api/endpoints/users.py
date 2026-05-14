from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/provision-batch", response_model=List[schemas.UserResponse])
async def provision_users(
    users_data: List[schemas.UserProvision],
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Upsert user records from Keycloak data (admin/designer only).
    Creates a stub user record for any Keycloak user not yet in the DB.
    This is called before dashboard assignment to satisfy FK constraints."""
    provisioned = []
    for u in users_data:
        user = db.query(models.User).filter(models.User.id == u.id).first()
        if not user:
            avatar = None
            if u.first_name:
                avatar = u.first_name[0].upper()
            elif u.username:
                avatar = u.username[0].upper()
            elif u.email:
                avatar = u.email[0].upper()
            user = models.User(
                id=u.id,
                email=u.email,
                username=u.username or u.email or u.id,
                full_name=u.full_name,
                first_name=u.first_name,
                last_name=u.last_name,
                role="viewer",
                avatar=avatar,
                is_active=True
            )
            db.add(user)
        provisioned.append(user)
    db.commit()
    for user in provisioned:
        db.refresh(user)
    return provisioned


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user info - auto-creates user if not exists"""
    
    # Try to find existing user
    user = db.query(models.User).filter(models.User.id == current_user.sub).first()
    
    if not user:
        # Auto-create user from Keycloak token
        user = models.User(
            id=current_user.sub,
            email=current_user.email,
            username=current_user.name or current_user.sub,
            full_name=current_user.name,
            first_name=current_user.name.split()[0] if current_user.name else None,
            last_name=" ".join(current_user.name.split()[1:]) if current_user.name and len(current_user.name.split()) > 1 else None,
            role=current_user.roles[0] if current_user.roles else "viewer",
            avatar=current_user.name[:2].upper() if current_user.name else current_user.sub[:2].upper(),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Get user by ID (admin/designer only)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/", response_model=List[schemas.UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """List all users (admin/designer only)"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """Update user (admin only)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user