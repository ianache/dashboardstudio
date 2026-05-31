import random
import string
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/editor-tools", tags=["editor-tools"])


def _gen_id():
    return 'tool-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))


@router.get("/", response_model=List[schemas.EditorToolResponse])
async def list_editor_tools(
    diagram_type: Optional[str] = Query(None, description="Filter by applicable diagram type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    await ensure_user_exists(current_user)
    q = db.query(models.EditorTool)
    if category:
        q = q.filter(models.EditorTool.category == category)
    tools = q.order_by(models.EditorTool.category, models.EditorTool.name).all()
    if diagram_type:
        # Filter in Python (JSON contains check)
        tools = [t for t in tools if diagram_type in (t.applicable_diagram_types or [])]
    return tools


@router.get("/{tool_id}", response_model=schemas.EditorToolResponse)
async def get_editor_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    tool = db.query(models.EditorTool).filter(models.EditorTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editor tool not found")
    return tool


@router.post("/", response_model=schemas.EditorToolResponse, status_code=status.HTTP_201_CREATED)
async def create_editor_tool(
    body: schemas.EditorToolCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    await ensure_user_exists(current_user)
    if db.query(models.EditorTool).filter(models.EditorTool.type == body.type).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tool type '{body.type}' already exists")
    tool = models.EditorTool(id=_gen_id(), **body.model_dump())
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool


@router.put("/{tool_id}", response_model=schemas.EditorToolResponse)
async def update_editor_tool(
    tool_id: str,
    body: schemas.EditorToolUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    tool = db.query(models.EditorTool).filter(models.EditorTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editor tool not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(tool, key, value)
    db.commit()
    db.refresh(tool)
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_editor_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    tool = db.query(models.EditorTool).filter(models.EditorTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editor tool not found")
    db.delete(tool)
    db.commit()
    return None


@router.post("/template-preview")
async def template_preview(
    request: schemas.TemplatePreviewRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Renders a Jinja2 template with provided sample data for UI preview.
    """
    try:
        from jinja2 import Environment
        env = Environment()
        template = env.from_string(request.template)
        
        # Prepare context: always provide 'data' and 'payload' keys
        # If data is a dict, also unpack it for direct access (backward compat)
        data = request.data if request.data is not None else {}
        context = {"data": data, "payload": data}
        if isinstance(data, dict):
            context.update(data)
            
        rendered = template.render(context)
        return {"rendered": rendered}
    except Exception as e:
        return {"error": str(e)}
