"""
Document routers - routing for document management endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from dana.api.core.database import get_db
from dana.api.core.schemas import DocumentRead, DocumentUpdate
from dana.api.services.document_service import get_document_service, DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: int | None = None,
    agent_id: int | None = None,
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload a document."""
    try:
        logger.info(f"Received document upload: {file.filename}")

        document = await document_service.upload_document(
            file=file.file, filename=file.filename, topic_id=topic_id, agent_id=agent_id, db_session=db
        )
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
