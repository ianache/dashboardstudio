from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/knowledge-spaces", tags=["knowledge-spaces"])


def _generate_id():
    import random
    return 'ks-' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


@router.post("/", response_model=schemas.KnowledgeSpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_space(
    space: schemas.KnowledgeSpaceCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new knowledge space (admin/designer only)"""
    # Ensure user exists in database before creating
    await ensure_user_exists(current_user)
    
    # Check if name already exists
    existing = db.query(models.KnowledgeSpace).filter(
        models.KnowledgeSpace.name == space.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Knowledge space with name '{space.name}' already exists"
        )
    
    db_space = models.KnowledgeSpace(
        id=_generate_id(),
        name=space.name,
        description=space.description,
        config=space.config,
        created_by=current_user.sub
    )
    db.add(db_space)
    db.commit()
    db.refresh(db_space)
    return db_space


@router.get("/", response_model=List[schemas.KnowledgeSpaceResponse])
async def list_knowledge_spaces(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all knowledge spaces"""
    # Ensure user exists
    await ensure_user_exists(current_user)
    
    spaces = db.query(models.KnowledgeSpace).all()
    return spaces


@router.get("/{space_id}", response_model=schemas.KnowledgeSpaceResponse)
async def get_knowledge_space(
    space_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get knowledge space by ID"""
    space = db.query(models.KnowledgeSpace).filter(
        models.KnowledgeSpace.id == space_id
    ).first()
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge space not found"
        )
    return space


@router.get("/by-name/{name}", response_model=schemas.KnowledgeSpaceResponse)
async def get_knowledge_space_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get knowledge space by name"""
    space = db.query(models.KnowledgeSpace).filter(
        models.KnowledgeSpace.name == name
    ).first()
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge space with name '{name}' not found"
        )
    return space


@router.get("/search/", response_model=List[schemas.KnowledgeSpaceResponse])
async def search_knowledge_spaces(
    q: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Search knowledge spaces by name or description"""
    await ensure_user_exists(current_user)
    
    spaces = db.query(models.KnowledgeSpace).filter(
        models.KnowledgeSpace.name.ilike(f"%{q}%") |
        models.KnowledgeSpace.description.ilike(f"%{q}%")
    ).all()
    
    return spaces


@router.put("/{space_id}", response_model=schemas.KnowledgeSpaceResponse)
async def update_knowledge_space(
    space_id: str,
    space_update: schemas.KnowledgeSpaceUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update knowledge space (admin/designer only)"""
    space = db.query(models.KnowledgeSpace).filter(
        models.KnowledgeSpace.id == space_id
    ).first()
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge space not found"
        )
    
    update_data = space_update.model_dump(exclude_unset=True)
    
    # Check if name is being updated and already exists
    if "name" in update_data and update_data["name"] != space.name:
        existing = db.query(models.KnowledgeSpace).filter(
            models.KnowledgeSpace.name == update_data["name"]
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Knowledge space with name '{update_data['name']}' already exists"
            )
    
    for key, value in update_data.items():
        setattr(space, key, value)
    
    db.commit()
    db.refresh(space)
    return space


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_space(
    space_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete knowledge space (admin/designer only)"""
    space = db.query(models.KnowledgeSpace).filter(
        models.KnowledgeSpace.id == space_id
    ).first()
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge space not found"
        )
    
    db.delete(space)
    db.commit()
    return None
