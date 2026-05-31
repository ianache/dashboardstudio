import os
import uuid
import json
import subprocess
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter()

# Configuration
STORAGE_DIR = "storage/models"
WORKER_SCRIPT = "app/runtime/ml_worker.py"

@router.post("/", response_model=schemas.MLModelResponse)
async def upload_model(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """
    Upload a scikit-learn .pkl model and extract its metadata.
    """
    if not file.filename.endswith(".pkl"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .pkl files are supported"
        )

    # 1. Save file to storage
    os.makedirs(STORAGE_DIR, exist_ok=True)
    model_id = str(uuid.uuid4())[:8]
    filename = f"{model_id}_{file.filename}"
    file_path = os.path.join(STORAGE_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Extract metadata using isolated worker
    try:
        result = subprocess.run(
            ["python", WORKER_SCRIPT, "--mode", "inspect", "--model-path", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        metadata = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        # Cleanup file if inspection fails
        if os.path.exists(file_path):
            os.remove(file_path)
        
        error_msg = e.stderr or str(e)
        try:
            error_json = json.loads(e.stdout)
            error_msg = error_json.get("error", error_msg)
        except:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to inspect model: {error_msg}"
        )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during model processing: {str(e)}"
        )

    # 3. Save to database
    db_model = models.MLModel(
        id=f"ml-{model_id}",
        name=name,
        filename=filename,
        sklearn_version=metadata.get("sklearn_version"),
        features=metadata.get("features", []),
        created_by=current_user.sub
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    
    return db_model

@router.get("/", response_model=List[schemas.MLModelResponse])
async def list_models(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all available ML models."""
    return db.query(models.MLModel).order_by(models.MLModel.created_at.desc()).all()

@router.get("/{model_id}", response_model=schemas.MLModelResponse)
async def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get specific model details."""
    model = db.query(models.MLModel).filter(models.MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete a model and its associated file."""
    model = db.query(models.MLModel).filter(models.MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Remove file
    file_path = os.path.join(STORAGE_DIR, model.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.delete(model)
    db.commit()
    return None
