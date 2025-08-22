"""
Document routers - routing for document management endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from dana.api.core.database import get_db
from dana.api.core.schemas import DocumentRead, DocumentUpdate, ExtractionDataRequest
from dana.api.services.document_service import get_document_service, DocumentService
from dana.api.services.extraction_service import get_extraction_service, ExtractionService
from dana.api.services.agent_deletion_service import get_agent_deletion_service, AgentDeletionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: int | None = Form(None),
    agent_id: int | None = Form(None),
    build_index: bool = Form(True),
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload a document and optionally build RAG index."""
    try:
        logger.info(f"Received document upload: {file.filename} (build_index={build_index})")

        document = await document_service.upload_document(
            file=file.file, filename=file.filename, topic_id=topic_id, agent_id=agent_id, db_session=db, build_index=build_index
        )

        if build_index and agent_id:
            logger.info(f"RAG index building started for agent {agent_id}")

        return document

    except Exception as e:
        logger.error(f"Error in document upload endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DocumentRead)
async def create_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    topic_id: int | None = Form(None),
    db: Session = Depends(get_db),
    document_service=Depends(get_document_service),
):
    """Create a document (legacy endpoint for compatibility)."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        logger.info(f"Received document creation: {file.filename}")

        document = await document_service.upload_document(
            file=file.file, filename=file.filename, topic_id=topic_id, agent_id=None, db_session=db
        )
        return document

    except Exception as e:
        logger.error(f"Error in document creation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: int, db: Session = Depends(get_db), document_service=Depends(get_document_service)):
    """Get a document by ID."""
    try:
        document = await document_service.get_document(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get document endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[DocumentRead])
async def list_documents(
    topic_id: int | None = None,
    agent_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    document_service=Depends(get_document_service),
):
    """List documents with optional filtering."""
    try:
        documents = await document_service.list_documents(topic_id=topic_id, agent_id=agent_id, limit=limit, offset=offset, db_session=db)
        return documents

    except Exception as e:
        logger.error(f"Error in list documents endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download")
async def download_document(document_id: int, db: Session = Depends(get_db), document_service=Depends(get_document_service)):
    """Download a document file."""
    try:
        document = await document_service.get_document(document_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get file path from document service
        file_path = await document_service.get_file_path(document_id, db)
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Document file not found")

        return FileResponse(path=file_path, filename=document.original_filename, media_type=document.mime_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download document endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: int, document_data: DocumentUpdate, db: Session = Depends(get_db), document_service=Depends(get_document_service)
):
    """Update a document."""
    try:
        updated_document = await document_service.update_document(document_id, document_data, db)
        if not updated_document:
            raise HTTPException(status_code=404, detail="Document not found")
        return updated_document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update document endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db), document_service=Depends(get_document_service)):
    """Delete a document."""
    try:
        success = await document_service.delete_document(document_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete document endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/{agent_id}/rebuild-index")
async def rebuild_agent_index(agent_id: int, db: Session = Depends(get_db), document_service=Depends(get_document_service)):
    """Rebuild RAG index for all documents belonging to an agent."""
    try:
        logger.info(f"Rebuilding RAG index for agent {agent_id}")

        # Trigger index rebuild for agent
        import asyncio

        asyncio.create_task(document_service._build_index_for_agent(agent_id, "", db))

        return {"message": f"RAG index rebuild started for agent {agent_id}", "status": "in_progress"}

    except Exception as e:
        logger.error(f"Error rebuilding index for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-extraction", response_model=DocumentRead)
async def save_extraction_data(
    request: ExtractionDataRequest,
    db: Session = Depends(get_db),
    extraction_service: ExtractionService = Depends(get_extraction_service),
):
    """Save extraction results as JSON file and create database relationship with source document."""
    try:
        logger.info(f"Saving extraction data for {request.original_filename}, source document ID: {request.source_document_id}")

        document = await extraction_service.save_extraction_json(
            original_filename=request.original_filename,
            extraction_results=request.extraction_results,
            source_document_id=request.source_document_id,
            db_session=db,
        )

        logger.info(f"Successfully saved extraction JSON file with ID: {document.id}")
        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in save extraction data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/extractions", response_model=list[DocumentRead])
async def get_document_extractions(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Get all extraction files for a specific document."""
    try:
        from dana.api.core.models import Document

        # Verify the source document exists
        source_document = db.query(Document).filter(Document.id == document_id).first()
        if not source_document:
            raise HTTPException(status_code=404, detail="Source document not found")

        # Get all extraction files for this document
        extraction_files = db.query(Document).filter(Document.source_document_id == document_id).all()

        result = []
        for doc in extraction_files:
            result.append(
                DocumentRead(
                    id=doc.id,
                    filename=doc.filename,
                    original_filename=doc.original_filename,
                    file_size=doc.file_size,
                    mime_type=doc.mime_type,
                    source_document_id=doc.source_document_id,
                    topic_id=doc.topic_id,
                    agent_id=doc.agent_id,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document extractions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-orphaned-files")
async def cleanup_orphaned_files(
    db: Session = Depends(get_db),
    deletion_service: AgentDeletionService = Depends(get_agent_deletion_service),
):
    """Clean up orphaned files that don't have corresponding database records."""
    try:
        logger.info("Starting cleanup of orphaned files")

        result = await deletion_service.cleanup_orphaned_files(db)

        logger.info(f"Cleanup completed: {result}")
        return {"message": "Cleanup completed successfully", "cleanup_stats": result}

    except Exception as e:
        logger.error(f"Error in cleanup orphaned files endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
