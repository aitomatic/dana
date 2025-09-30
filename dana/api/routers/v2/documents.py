import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from dana.api.core.database import get_db
from dana.api.core.schemas import DocumentRead, ExtractionDataRequest
from dana.api.services.document_service import get_document_service, DocumentService
from dana.api.services.extraction_service import get_extraction_service, ExtractionService
from dana.api.routers.v1.extract_documents import deep_extract
from dana.api.core.schemas import DeepExtractionRequest, ExtractionResponse
from dana.api.background.task_manager import get_task_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUploadResponse(BaseModel):
    success: bool
    document: DocumentRead | None = None
    message: str | None = None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: int | None = Form(None),
    agent_id: int | None = Form(None),
    build_index: bool = Form(True),
    allow_duplicate: bool = Form(False),
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload a document with duplicate checking and background deep extraction."""
    try:
        logger.info(f"Received document upload: {file.filename} (allow_duplicated={allow_duplicate})")

        # Check for duplicates if not allowing duplicates
        if not allow_duplicate and file.filename:
            existing_document = await document_service.check_document_exists(original_filename=file.filename, db_session=db)
            if existing_document:
                logger.info(f"Document {file.filename} already exists, returning success=False")
                return DocumentUploadResponse(
                    success=False,
                    document=None,
                    message=f"Document '{file.filename}' already exists. Use allow_duplicated=True to force upload.",
                )

        # Upload the document
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        document = await document_service.upload_document(
            file=file.file, filename=file.filename, topic_id=topic_id, agent_id=agent_id, db_session=db, build_index=build_index
        )

        if build_index and agent_id:
            logger.info(f"RAG index building started for agent {agent_id}")

        # Perform deep_extract with use_deep_extraction=False
        result: ExtractionResponse = await deep_extract(
            DeepExtractionRequest(document_id=document.id, use_deep_extraction=False, config={}), db=db
        )
        pages = result.file_object.pages

        # Save extraction data
        await save_extraction_data(
            ExtractionDataRequest(
                original_filename=document.original_filename,
                source_document_id=document.id,
                extraction_results={
                    "original_filename": document.original_filename,
                    "extraction_date": datetime.now().isoformat(),
                    "total_pages": result.file_object.total_pages,
                    "documents": [{"text": page.page_content, "page_number": page.page_number} for page in pages],
                },
            ),
            db=db,
            extraction_service=get_extraction_service(),
        )

        # Create background task for deep extraction with use_deep_extraction=True
        task_manager = get_task_manager()
        await task_manager.add_deep_extract_task(document_id=document.id)

        logger.info(f"Document uploaded successfully with ID: {document.id}")
        return DocumentUploadResponse(success=True, document=document, message="Document uploaded successfully")

    except Exception as e:
        logger.error(f"Error in document upload endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
