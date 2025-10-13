"""
Domain Knowledge routers - API endpoints for managing agent domain knowledge trees.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dana.lang.api.core.database import get_db
from dana.lang.api.core.schemas_v2 import (
    KnowledgePackAssociateDocumentsRequest,
    KnowledgePackAssociateDocumentsResponse,
    KnowledgePackCreateRequest,
    KnowledgePackCreateResponse,
    KnowledgePackDeleteResponse,
    KnowledgePackGetResponse,
    KnowledgePackUpdateRequest,
    KnowledgePackUpdateResponse,
    PaginatedKnowledgePackResponse,
)
from dana.lang.api.repositories import get_domain_knowledge_repo, AbstractDomainKnowledgeRepo
from ..ws.domain_knowledge_ws import domain_knowledge_ws_notifier
from fastapi import WebSocket
from fastapi.concurrency import run_until_first_complete

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{knowledge_id}", response_model=KnowledgePackGetResponse)
async def get_knowledge_pack(
    knowledge_id: int, repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo), db: Session = Depends(get_db)
):
    """
    Get the current domain knowledge tree for a knowledge.
    """
    try:
        tree = await repo.get_kp_tree(kp_id=knowledge_id)
        return KnowledgePackGetResponse(success=True, message="Knowledge pack retrieved successfully", data=tree)
    except Exception as e:
        logger.error(f"Error getting knowledge pack {knowledge_id}: {e}")
        return KnowledgePackGetResponse(success=False, message="Failed to retrieve knowledge pack", error=str(e))


@router.get("/", response_model=PaginatedKnowledgePackResponse)
async def list_knowledge_packs(
    limit: int = 20,
    offset: int = 0,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    List all knowledge packs with optional filtering.
    """
    return await repo.list_kp(limit=limit, offset=offset, db=db)


@router.post("/create", response_model=KnowledgePackCreateResponse)
async def create_knowledge_pack(
    request: KnowledgePackCreateRequest,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Initialize a knowledge pack with optional document associations.
    """
    try:
        metadata = request.specialization.model_dump()

        # Add associated documents to metadata if provided
        if request.document_ids:
            metadata["associated_documents"] = request.document_ids

        kp = await repo.create_kp(kp_metadata=metadata, db=db)
        return KnowledgePackCreateResponse(success=True, message="Knowledge pack created successfully", data=kp)
    except Exception as e:
        logger.error(f"Error creating knowledge pack: {e}")
        return KnowledgePackCreateResponse(success=False, message="Failed to create knowledge pack", error=str(e))


@router.post("/update", response_model=KnowledgePackUpdateResponse)
async def update_knowledge_pack(
    request: KnowledgePackUpdateRequest,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Update a knowledge pack.
    """
    try:
        metadata = request.specialization.model_dump()
        kp = await repo.update_kp(kp_id=request.kp_id, kp_metadata=metadata, db=db)
        return KnowledgePackUpdateResponse(success=True, message="Knowledge pack updated successfully", data=kp)
    except ValueError as e:
        logger.error(f"Bad request error updating knowledge pack: {e}")
        return KnowledgePackUpdateResponse(success=False, message="Invalid request data", error=str(e))
    except Exception as e:
        logger.error(f"Internal server error updating knowledge pack: {e}")
        return KnowledgePackUpdateResponse(success=False, message="Failed to update knowledge pack", error=str(e))


@router.websocket("/ws/{knowledge_id}")
async def send_chat_update_msg(knowledge_id: str, websocket: WebSocket):
    await run_until_first_complete(
        (domain_knowledge_ws_notifier.run_ws_loop_forever, {"websocket": websocket, "websocket_id": knowledge_id}),
    )


@router.get("/test-ws/{knowledge_id}")
async def test_ws(knowledge_id: str, message: str):
    await domain_knowledge_ws_notifier.send_update_msg(knowledge_id, message)


@router.post("/{knowledge_id}/documents/associate", response_model=KnowledgePackAssociateDocumentsResponse)
async def associate_documents_to_knowledge_pack(
    knowledge_id: int,
    request: KnowledgePackAssociateDocumentsRequest,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Associate documents with a knowledge pack.
    """
    try:
        # Use the repository method to associate documents
        await repo.associate_documents_to_kp(kp_id=knowledge_id, document_ids=request.document_ids, db=db)

        return KnowledgePackAssociateDocumentsResponse(
            success=True,
            message=f"Successfully associated {len(request.document_ids)} documents with knowledge pack {knowledge_id}",
            associated_count=len(request.document_ids),
            error=None,
        )

    except ValueError as e:
        logger.error(f"Bad request error associating documents: {e}")
        return KnowledgePackAssociateDocumentsResponse(success=False, message=str(e), associated_count=0, error=str(e))
    except Exception as e:
        logger.error(f"Error associating documents with knowledge pack {knowledge_id}: {e}")
        return KnowledgePackAssociateDocumentsResponse(success=False, message="Internal server error", associated_count=0, error=str(e))


@router.delete("/{knowledge_id}", response_model=KnowledgePackDeleteResponse)
async def delete_knowledge_pack(
    knowledge_id: int,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Delete a knowledge pack and all associated resources.
    """
    try:
        await repo.delete_kp(kp_id=knowledge_id, db=db)
        return KnowledgePackDeleteResponse(
            success=True,
            message=f"Successfully deleted knowledge pack {knowledge_id}",
            error=None,
        )
    except ValueError as e:
        logger.error(f"Bad request error deleting knowledge pack: {e}")
        return KnowledgePackDeleteResponse(success=False, message=str(e), error=str(e))
    except Exception as e:
        logger.error(f"Error deleting knowledge pack {knowledge_id}: {e}")
        return KnowledgePackDeleteResponse(success=False, message="Internal server error", error=str(e))
