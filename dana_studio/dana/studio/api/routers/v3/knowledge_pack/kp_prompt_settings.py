from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dana.studio.api.core.database import get_db
from dana.studio.api.repositories import get_domain_knowledge_repo
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/{knowledge_id}/prompt-settings", tags=["knowledge-pack-prompt-settings"])


class PromptOverrideRequest(BaseModel):
    """Request to set a prompt override for a knowledge pack."""

    value: str


@router.get("")
async def get_kp_prompt_overrides(
    knowledge_id: int,
    kb_repo: type = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """Get all prompt overrides for a knowledge pack."""
    kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge pack not found")

    kp_metadata = kb.kp_metadata or {}
    prompt_overrides = kp_metadata.get("prompt_overrides", {})

    return {
        "success": True,
        "knowledge_id": knowledge_id,
        "prompt_overrides": prompt_overrides,
    }


@router.put("/{category}/{key}")
async def set_kp_prompt_override(
    knowledge_id: int,
    category: str,
    key: str,
    request: PromptOverrideRequest,
    kb_repo: type = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """Set a prompt override for a knowledge pack."""
    kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge pack not found")

    kp_metadata = kb.kp_metadata or {}
    if "prompt_overrides" not in kp_metadata:
        kp_metadata["prompt_overrides"] = {}

    if category not in kp_metadata["prompt_overrides"]:
        kp_metadata["prompt_overrides"][category] = {}

    kp_metadata["prompt_overrides"][category][key] = request.value

    await kb_repo.update_kp(knowledge_id, kp_metadata=kp_metadata, db=db)

    return {
        "success": True,
        "message": f"Prompt override {category}.{key} set for knowledge pack {knowledge_id}",
        "value": request.value,
    }


@router.delete("/{category}/{key}")
async def remove_kp_prompt_override(
    knowledge_id: int,
    category: str,
    key: str,
    kb_repo: type = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """Remove a prompt override for a knowledge pack."""
    kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge pack not found")

    kp_metadata = kb.kp_metadata or {}
    prompt_overrides = kp_metadata.get("prompt_overrides", {})

    if category in prompt_overrides and key in prompt_overrides[category]:
        del prompt_overrides[category][key]

        # Clean up empty categories
        if not prompt_overrides[category]:
            del prompt_overrides[category]

        kp_metadata["prompt_overrides"] = prompt_overrides
        await kb_repo.update_kp(knowledge_id, kp_metadata=kp_metadata, db=db)

        return {
            "success": True,
            "message": f"Prompt override {category}.{key} removed for knowledge pack {knowledge_id}",
        }
    else:
        raise HTTPException(status_code=404, detail=f"Prompt override {category}.{key} not found for knowledge pack {knowledge_id}")
