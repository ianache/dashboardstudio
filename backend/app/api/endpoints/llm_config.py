from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_role, TokenData, ensure_user_exists
from app.core.encryption import encrypt_value, decrypt_value
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/llm-config", tags=["llm-config"])


def _generate_id():
    import random
    return 'llm-' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))


@router.get("/", response_model=List[schemas.LlmConfigResponse])
async def list_llm_configs(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all LLM configurations for current user with decrypted API keys."""
    # Ensure user exists in database
    await ensure_user_exists(current_user)
    
    configs = db.query(models.LlmConfig).filter(
        models.LlmConfig.created_by == current_user.sub
    ).all()
    
    # Decrypt API keys for response
    for config in configs:
        if config.api_key:
            try:
                config.api_key = decrypt_value(config.api_key)
            except ValueError:
                config.api_key = ""
    
    return configs


@router.get("/providers", response_model=List[schemas.LlmProviderInfo])
async def get_llm_providers(
    current_user: TokenData = Depends(get_current_user)
):
    """Get list of supported LLM providers with their metadata."""
    return [
        {
            "id": "anthropic",
            "label": "Anthropic Claude",
            "icon": "🅰️",
            "api_key_label": "API Key Anthropic",
            "api_key_placeholder": "sk-ant-...",
            "docs_url": "https://console.anthropic.com/"
        },
        {
            "id": "gemini",
            "label": "Google Gemini",
            "icon": "🔷",
            "api_key_label": "API Key Google AI Studio",
            "api_key_placeholder": "AIza...",
            "docs_url": "https://aistudio.google.com/apikey"
        },
        {
            "id": "moonshot",
            "label": "Moonshot",
            "icon": "🌙",
            "api_key_label": "API Key Moonshot",
            "api_key_placeholder": "sk-...",
            "docs_url": "https://platform.moonshot.ai/"
        },
        {
            "id": "groq",
            "label": "Groq",
            "icon": "⚡",
            "api_key_label": "API Key Groq",
            "api_key_placeholder": "gsk_...",
            "docs_url": "https://console.groq.com/"
        }
    ]


@router.post("/", response_model=schemas.LlmConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_llm_config(
    config: schemas.LlmConfigCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Create or update LLM configuration for a provider (admin/designer only).
    
    If a config for the same provider already exists for this user, it will be updated.
    """
    # Ensure user exists in database before creating config
    await ensure_user_exists(current_user)
    
    # Check if config already exists for this provider and user
    existing = db.query(models.LlmConfig).filter(
        models.LlmConfig.provider == config.provider,
        models.LlmConfig.created_by == current_user.sub
    ).first()
    
    if existing:
        # Update existing
        encrypted_key = encrypt_value(config.api_key)
        existing.api_key = encrypted_key
        db.commit()
        # Decrypt for response
        existing.api_key = config.api_key
        return existing
    else:
        # Create new
        db_config = models.LlmConfig(
            id=_generate_id(),
            provider=config.provider,
            api_key=encrypt_value(config.api_key),
            created_by=current_user.sub
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        # Decrypt for response
        db_config.api_key = config.api_key
        return db_config


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    provider: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete LLM configuration for a provider (admin/designer only)."""
    config = db.query(models.LlmConfig).filter(
        models.LlmConfig.provider == provider,
        models.LlmConfig.created_by == current_user.sub
    ).first()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    
    db.delete(config)
    db.commit()
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_llm_configs(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(["admin", "designer"]))
):
    """Delete all LLM configurations for current user (admin/designer only)."""
    db.query(models.LlmConfig).filter(
        models.LlmConfig.created_by == current_user.sub
    ).delete()
    db.commit()
    return None
