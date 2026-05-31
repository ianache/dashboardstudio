from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
import httpx
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/users", tags=["users"])


async def _keycloak_admin_token() -> str:
    """Get a service-account token for Keycloak Admin API access."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            settings.keycloak_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


@router.get("/search")
async def search_keycloak_users(
    q: str = Query(..., min_length=2),
    max: int = Query(20, le=50),
    current_user: TokenData = Depends(require_role(["admin", "designer"])),
):
    """Search users in Keycloak by name, email or username."""
    settings = get_settings()
    try:
        token = await _keycloak_admin_token()
        url = (
            f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"
            f"/users?search={q}&max={max}"
        )
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            raw = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Keycloak error: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Keycloak: {str(e)}",
        )

    return [
        {
            "id": u.get("id"),
            "username": u.get("username", ""),
            "email": u.get("email", ""),
            "first_name": u.get("firstName", ""),
            "last_name": u.get("lastName", ""),
            "full_name": f"{u.get('firstName', '')} {u.get('lastName', '')}".strip()
                or u.get("username", ""),
        }
        for u in raw
    ]


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