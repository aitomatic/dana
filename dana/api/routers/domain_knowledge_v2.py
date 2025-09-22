"""
Domain Knowledge routers - API endpoints for managing agent domain knowledge trees.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import (
    DomainKnowledgeTree,
)
from dana.api.repositories import get_domain_knowledge_repo, AbstractDomainKnowledgeRepo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["domain-knowledge"])


@router.get("/{knowledge_id}", response_model=DomainKnowledgeTree | dict)
async def get_knowledge_pack(
    knowledge_id: int, repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo), db: Session = Depends(get_db)
):
    """
    Get the current domain knowledge tree for a knowledge.
    """
    try:
        kp = await repo.get_kp(knowledge_id, db=db)
        return kp
    except Exception as e:
        logger.error(f"Error getting knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
