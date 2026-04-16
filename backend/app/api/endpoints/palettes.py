import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

logger = logging.getLogger(__name__)

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
    # Built-in fallback colors keyed by palette ID
    built_in_colors = {
        "default": ["#5470c6","#91cc75","#fac858","#ee6666","#73c0de","#3ba272","#fc8452","#9a60b4","#ea7ccc","#2f4554"],
        "ocean":   ["#006994","#0096c7","#48cae4","#90e0ef","#ade8f4","#0077b6","#023e8a","#03045e","#caf0f8","#00b4d8"],
        "sunset":  ["#ff6b35","#f7931e","#ffd23f","#ee4266","#540d6e","#f7b801","#f18701","#d95d39","#c73e1d","#2e1a47"],
        "forest":  ["#2d6a4f","#40916c","#52b788","#74c69d","#95d5b2","#1b4332","#081c15","#b7e4c7","#d8f3dc","#40916c"],
        "pastel":  ["#ffb3ba","#ffdfba","#ffffba","#baffc9","#bae1ff","#eecbff","#ffccf9","#c4faf8","#fdc5f5","#85e3ff"],
        "vivid":   ["#ff006e","#fb5607","#ffbe0b","#8338ec","#3a86ff","#06ffa5","#ff4365","#00d9ff","#bd00ff","#ff9f1c"],
        "earth":   ["#8b4513","#d2691e","#cd853f","#deb887","#f4a460","#a0522d","#bc8f8f","#f5deb3","#daa520","#8b7355"],
        "mono":    ["#1a1a2e","#16213e","#0f3460","#533483","#e94560","#162447","#1f4068","#1b1b2f","#4f3b78","#9d65c9"],
    }

    try:
        palettes = db.query(models.ColorPalette).all()
    except Exception as e:
        logger.warning(f"Could not query color_palettes table: {e}")
        palettes = []

    if not palettes:
        # No rows at all — return built-ins as virtual objects
        return [
            schemas.ColorPaletteResponse(
                id=pid,
                label=colors[0] if False else _BUILTIN_LABELS.get(pid, pid),
                colors=colors,
                is_default=(pid == "default"),
                created_by=None,
                created_at=None,
                updated_at=None
            ) for pid, colors in built_in_colors.items()
        ]

    # Rows exist but colors may be NULL (migration stored them as NULL)
    # Patch in the built-in colors for any palette whose colors column is empty/null
    for p in palettes:
        if not p.colors and p.id in built_in_colors:
            p.colors = built_in_colors[p.id]

    return palettes


_BUILTIN_LABELS = {
    "default": "Predeterminada",
    "ocean":   "Océano",
    "sunset":  "Atardecer",
    "forest":  "Bosque",
    "pastel":  "Pastel",
    "vivid":   "Vívida",
    "earth":   "Tierra",
    "mono":    "Monocromática",
}


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