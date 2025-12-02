from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dana.studio.api.core.database import get_db
from dana.studio.api.repositories import get_application_settings_repo
from dana.studio.api.core.schemas_v2 import (
    PromptSetting,
    PromptSettingsResponse,
    PromptUpdateRequest,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["prompt-settings"])


@router.get("", response_model=PromptSettingsResponse)
async def get_all_prompt_settings(
    db: Session = Depends(get_db),
):
    """Get all prompt settings organized by category."""
    settings_repo = get_application_settings_repo()
    all_settings = await settings_repo.get_all_settings(db)

    # Convert to response format
    settings_dict = {}
    categories = []

    for category, settings_list in all_settings.items():
        categories.append(category)
        settings_dict[category] = [
            PromptSetting(
                category=category,
                key=s.key,
                full_key=s.full_key,
                value=s.value,
                name=s.name or s.key,
                description=s.description or "",
                placeholders=s.placeholders or [],
                placeholder_examples=s.placeholder_examples or {},
                default_value=s.default_value,
                applies_to=s.applies_to or "global",
                is_active=s.is_active,
            )
            for s in settings_list
        ]

    return PromptSettingsResponse(settings=settings_dict, categories=categories)


@router.get("/{category}/{key}")
async def get_prompt_setting(
    category: str,
    key: str,
    db: Session = Depends(get_db),
):
    """Get a specific prompt setting."""
    settings_repo = get_application_settings_repo()
    setting = await settings_repo.get_setting_with_metadata(category, key, db)

    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting {category}.{key} not found")

    return {
        "success": True,
        "category": setting.category,
        "key": setting.key,
        "full_key": setting.full_key,
        "value": setting.value,
        "name": setting.name,
        "description": setting.description,
        "placeholders": setting.placeholders or [],
        "placeholder_examples": setting.placeholder_examples or {},
        "default_value": setting.default_value,
    }


@router.put("/{category}/{key}")
async def update_prompt_setting(
    category: str,
    key: str,
    request: PromptUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update a prompt setting."""
    settings_repo = get_application_settings_repo()
    setting = await settings_repo.set_setting(
        category=category,
        key=key,
        value=request.value,
        name=request.name,
        description=request.description,
        db=db,
    )

    return {
        "success": True,
        "message": f"Prompt setting {category}.{key} updated",
        "setting": {
            "full_key": setting.full_key,
            "value": setting.value,
        },
    }


@router.post("/{category}/{key}/reset")
async def reset_prompt_setting(
    category: str,
    key: str,
    db: Session = Depends(get_db),
):
    """Reset a prompt setting to its default value."""
    settings_repo = get_application_settings_repo()
    setting = await settings_repo.get_setting_with_metadata(category, key, db)

    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting {category}.{key} not found")

    if not setting.default_value:
        raise HTTPException(status_code=400, detail="No default value available for this setting")

    setting.value = setting.default_value
    db.commit()
    db.refresh(setting)

    return {
        "success": True,
        "message": f"Prompt setting {category}.{key} reset to default",
        "value": setting.value,
    }
