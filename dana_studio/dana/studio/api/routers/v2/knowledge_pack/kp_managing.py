"""
Domain Knowledge routers - API endpoints for managing agent domain knowledge trees.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
import tarfile
import tempfile

from dana.studio.api.core.database import get_db
from dana.studio.api.core.schemas_v2 import (
    KnowledgePackAssociateDocumentsRequest,
    KnowledgePackAssociateDocumentsResponse,
    KnowledgePackCreateRequest,
    KnowledgePackCreateResponse,
    KnowledgePackDeleteResponse,
    KnowledgePackGetResponse,
    KnowledgePackOutput,
    KnowledgePackUpdateRequest,
    KnowledgePackUpdateResponse,
    PaginatedKnowledgePackResponse,
    InterviewAnalysisGenerateRequest,
    InterviewAnalysisGenerateResponse,
    InterviewAnalysisGetResponse,
    KnowledgePackAnalysisData,
)
from dana.studio.api.repositories import (
    get_domain_knowledge_repo,
    AbstractDomainKnowledgeRepo,
)
from dana.studio.api.repositories.config import KNOW_FOLDER_NAME
from dana.studio.api.services.knowledge_pack.postprocess_interview_session.postprocessor import (
    generate_kp_analysis,
)
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
    Get the knowledge pack with both metadata and tree structure.
    """
    try:
        # Get knowledge pack metadata
        kp = await repo.get_kp(kp_id=knowledge_id, db=db)
        if not kp:
            return KnowledgePackGetResponse(success=False, message="Knowledge pack not found", error="Not found")

        # Get knowledge pack tree structure
        tree = await repo.get_kp_tree(kp_id=knowledge_id)

        # Combine metadata and tree into a single response
        kp_dict = kp.model_dump()
        kp_dict["tree"] = tree
        kp_with_tree = KnowledgePackOutput(**kp_dict)

        return KnowledgePackGetResponse(success=True, message="Knowledge pack retrieved successfully", data=kp_with_tree)
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


@router.post("/{knowledge_id}/interview-analysis/generate", response_model=InterviewAnalysisGenerateResponse)
async def generate_interview_analysis(
    knowledge_id: int,
    request: InterviewAnalysisGenerateRequest,
    domain_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Generate LLM-enhanced analysis for all templates in a knowledge pack.
    Uses per-topic caching for efficiency.

    This endpoint:
    1. Gets all templates for the knowledge pack
    2. For each template, finds all interview_notes.md in sessions
    3. Groups similar topics across sessions
    4. Uses LLM to analyze each topic (consensus + contradictions)
    5. Caches each topic individually (automatic cache invalidation on content change)
    6. Returns structured JSON with all templates
    """
    try:
        # Get knowledge pack to verify it exists
        kp = await domain_repo.get_kp(kp_id=knowledge_id, db=db)
        if not kp:
            return InterviewAnalysisGenerateResponse(
                success=False, message=f"Knowledge pack {knowledge_id} not found", error="Knowledge pack not found"
            )

        # Get all templates for this knowledge pack
        templates = kp.interview_templates

        if not templates:
            logger.warning(f"No templates found for knowledge pack {knowledge_id}")
            return InterviewAnalysisGenerateResponse(
                success=True,
                message="No templates found in this knowledge pack",
                data=KnowledgePackAnalysisData(kp_id=knowledge_id, generated_at=datetime.now().isoformat(), templates=[]),
            )

        logger.info(f"Generating interview analysis for KP {knowledge_id} with {len(templates)} templates")

        # Generate analysis (caching handled internally per topic)
        analysis_data = await generate_kp_analysis(
            kp_id=knowledge_id, templates=templates, use_llm=request.use_llm, llm_config=request.llm_config
        )

        total_templates = len(analysis_data["templates"])
        logger.info(f"Analysis generated for {total_templates} templates")

        return InterviewAnalysisGenerateResponse(
            success=True,
            message=f"Interview analysis completed for {total_templates} template{'s' if total_templates != 1 else ''}",
            data=KnowledgePackAnalysisData.model_validate(analysis_data),
        )

    except Exception as e:
        logger.error(f"Error generating interview analysis: {e}", exc_info=True)
        return InterviewAnalysisGenerateResponse(success=False, message="Failed to generate interview analysis", error=str(e))


@router.get("/{knowledge_id}/interview-analysis", response_model=InterviewAnalysisGetResponse)
async def get_interview_analysis(
    knowledge_id: int,
    domain_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Get interview analysis for all templates. Uses per-topic caching automatically.

    Note: No force_refresh needed - cache invalidates automatically when content changes.
    Each topic is cached separately based on the hash of expert insights.

    Returns structured JSON with all templates, each containing sessions and unified_report per topic.
    """
    try:
        # Get knowledge pack to verify it exists
        kp = await domain_repo.get_kp(kp_id=knowledge_id, db=db)
        if not kp:
            return InterviewAnalysisGetResponse(
                success=False, message=f"Knowledge pack {knowledge_id} not found", error="Knowledge pack not found"
            )

        # Get all templates for this knowledge pack
        templates = kp.interview_templates

        if not templates:
            logger.warning(f"No templates found for knowledge pack {knowledge_id}")
            return InterviewAnalysisGetResponse(
                success=True,
                message="No templates found in this knowledge pack",
                data=KnowledgePackAnalysisData(kp_id=knowledge_id, generated_at=datetime.now().isoformat(), templates=[]),
                cached=False,
            )

        # Generate analysis (will use cache automatically where valid)
        analysis_data = await generate_kp_analysis(
            kp_id=knowledge_id,
            templates=templates,
            use_llm=True,  # Default to LLM for GET requests
        )

        return InterviewAnalysisGetResponse(
            success=True,
            message="Interview analysis retrieved successfully",
            data=KnowledgePackAnalysisData.model_validate(analysis_data),
            cached=False,  # Individual topics may be cached
        )

    except Exception as e:
        logger.error(f"Error getting interview analysis: {e}", exc_info=True)
        return InterviewAnalysisGetResponse(success=False, message="Failed to retrieve interview analysis", error=str(e))


@router.get("/{knowledge_id}/download-knows")
async def download_knowledge_pack_knows(
    knowledge_id: int,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Download knowledge pack knows folder as tar.gz archive.
    """
    try:
        # Get knowledge pack to verify it exists
        kp = await repo.get_kp(kp_id=knowledge_id, db=db)
        if not kp:
            raise HTTPException(status_code=404, detail=f"Knowledge pack {knowledge_id} not found")

        # Get knowledge pack folder path
        kp_folder = repo.get_knowledge_pack_folder(knowledge_id)
        if not kp_folder or not kp_folder.exists():
            raise HTTPException(status_code=404, detail=f"Knowledge pack folder not found for KP {knowledge_id}")

        # Locate knows folder
        knows_dir = kp_folder / KNOW_FOLDER_NAME
        if not knows_dir.exists():
            raise HTTPException(status_code=404, detail=f"Knows folder not found for knowledge pack {knowledge_id}")

        # Create temporary tar.gz file
        temp_tar = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
        temp_tar.close()

        # Create tar.gz archive
        with tarfile.open(temp_tar.name, "w:gz") as tar:
            # Add the knows directory to the archive
            tar.add(knows_dir, arcname=KNOW_FOLDER_NAME)

        # Read the tar.gz file into memory
        with open(temp_tar.name, "rb") as f:
            tar_content = f.read()

        # Clean up temporary file
        Path(temp_tar.name).unlink(missing_ok=True)

        # Return streaming response
        filename = f"kp_{knowledge_id}_knows.tar.gz"
        return StreamingResponse(
            iter([tar_content]), media_type="application/gzip", headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading knows folder for knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download knows folder: {str(e)}")
