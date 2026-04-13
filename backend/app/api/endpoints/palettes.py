from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/palettes", tags=["color-palettes"])


def _generate_id():
    import random
    return 'pal_' + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))


@router.post("/", response_model=schemas.ColorPaletteResponse, status_code=status.HTTP_201_CREATED)
async def create_palette(
    palette: schemas.ColorPaletteCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create a new color palette (admin/designer only)"""
    # Ensure user exists in database
    await ensure_user_exists(current_user)
    
    if palette.is_default:
        db.query(models.ColorPalette).update({models.ColorPalette.is_default: False})
    
    db_palette = models.ColorPalette(
        id=_generate_id(),
        label=palette.label,
        colors=palette.colors,
        is_default=palette.is_default,
        created_by=current_user.sub
    )
    db.add(db_palette)
    db.commit()
    db.refresh(db_palette)
    return db_palette


@router.get("/", response_model=List[schemas.ColorPaletteResponse])
async def list_palettes(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all color palettes"""
    palettes = db.query(models.ColorPalette).all()
    
    # Include built-in palettes if none exist
    if not palettes:
        built_in = [
            {"id": "default", "label": "Predeterminada", "colors": ["#1890ff","#52c41a","#faad14","#f5222d","#722ed1","#13c2c2","#fa8c16","#eb2f96","#2f54eb","#a0d911"]},
            {"id": "ocean", "label": "Océano", "colors": ["#003f5c","#2f6b9a","#1890ff","#36cfc9","#87e8de","#006d75","#08979c","#13c2c2","#5cdbd3","#b5f5ec"]},
            {"id": "sunset", "label": "Atardecer", "colors": ["#7b2d00","#d4380d","#fa541c","#fa8c16","#faad14","#ffc53d","#ffe58f","#eb2f96","#c41d7f","#9e1068"]},
            {"id": "forest", "label": "Bosque", "colors": ["#092b00","#135200","#237804","#389e0d","#52c41a","#73d13d","#95de64","#b7eb8f","#6abe39","#2d8653"]},
        ]
        return [schemas.ColorPaletteResponse(id=p["id"], label=p["label"], colors=p["colors"], is_default=p["id"]=="default", created_by=None, created_at=None, updated_at=None) for p in built_in]
    
    return palettes


@router.get("/{palette_id}", response_model=schemas.ColorPaletteResponse)
async def get_palette(
    palette_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get palette by ID"""
    palette = db.query(models.ColorPalette).filter(models.ColorPalette.id == palette_id).first()
    if not palette:
        # Check built-in
        built_in_map = {
            "default": {"label": "Predeterminada", "colors": ["#1890ff","#52c41a","#faad14","#f5222d","#722ed1","#13c2c2","#fa8c16","#eb2f96","#2f54eb","#a0d911"]},
            "ocean": {"label": "Océano", "colors": ["#003f5c","#2f6b9a","#1890ff","#36cfc9","#87e8de","#006d75","#08979c","#13c2c2","#5cdbd3","#b5f5ec"]},
            "sunset": {"label": "Atardecer", "colors": ["#7b2d00","#d4380d","#fa541c","#fa8c16","#faad14","#ffc53d","#ffe58f","#eb2f96","#c41d7f","#9e1068"]},
            "forest": {"label": "Bosque", "colors": ["#092b00","#135200","#237804","#389e0d","#52c41a","#73d13d","#95de64","#b7eb8f","#6abe39","#2d8653"]},
            "pastel": {"label": "Pastel", "colors": ["#91caff","#b7eb8f","#ffe58f","#ffadd2","#d3adf7","#87e8de","#ffd591","#ffa39e","#adc6ff","#d9f7be"]},
            "vivid": {"label": "Vívida", "colors": ["#003eb3","#0050b3","#1890ff","#00b5d8","#00c9a7","#52c41a","#fadb14","#fa8c16","#f5222d","#eb2f96"]},
            "earth": {"label": "Tierra", "colors": ["#3b1f0e","#6b3a2a","#9c5634","#c87941","#d4935a","#e0b07b","#a8764b","#7c5c3c","#5c3d2e","#2d2010"]},
            "mono": {"label": "Monocromática", "colors": ["#003a8c","#0050b3","#096dd9","#1890ff","#40a9ff","#69c0ff","#91d5ff","#bae7ff","#0d47a1","#1565c0"]},
        }
        if palette_id in built_in_map:
            p = built_in_map[palette_id]
            return schemas.ColorPaletteResponse(id=palette_id, label=p["label"], colors=p["colors"], is_default=palette_id=="default", created_by=None, created_at=None, updated_at=None)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palette not found")
    return palette


@router.put("/{palette_id}", response_model=schemas.ColorPaletteResponse)
async def update_palette(
    palette_id: str,
    palette_update: schemas.ColorPaletteUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Update palette (admin/designer only)"""
    palette = db.query(models.ColorPalette).filter(models.ColorPalette.id == palette_id).first()
    if not palette:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palette not found")
    
    update_data = palette_update.model_dump(exclude_unset=True)
    
    if update_data.get("is_default"):
        db.query(models.ColorPalette).filter(models.ColorPalette.id != palette_id).update({models.ColorPalette.is_default: False})
    
    for key, value in update_data.items():
        setattr(palette, key, value)
    
    db.commit()
    db.refresh(palette)
    return palette


@router.delete("/{palette_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_palette(
    palette_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete palette (admin/designer only)"""
    palette = db.query(models.ColorPalette).filter(models.ColorPalette.id == palette_id).first()
    if not palette:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palette not found")
    
    db.delete(palette)
    db.commit()
    return None


@router.post("/{palette_id}/default", response_model=schemas.ColorPaletteResponse)
async def set_default_palette(
    palette_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Set palette as default (admin/designer only)"""
    palette = db.query(models.ColorPalette).filter(models.ColorPalette.id == palette_id).first()
    if not palette:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Palette not found")
    
    db.query(models.ColorPalette).update({models.ColorPalette.is_default: False})
    palette.is_default = True
    
    db.commit()
    db.refresh(palette)
    return palette