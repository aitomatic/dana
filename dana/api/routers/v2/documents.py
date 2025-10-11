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
from dana.api.repositories import get_background_task_repo, AbstractBackgroundTaskRepo, get_document_repo, AbstractDocumentRepo
from dana.api.core.schemas_v2 import BackgroundTaskResponse, ExtractionOutput
from dana.common.sys_resource.rag import get_global_rag_resource, RAGResourceV2


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentUploadResponse(BaseModel):
    success: bool
    document: DocumentRead | None = None
    message: str | None = None
    task_id: int | None = None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    topic_id: int | None = Form(None),
    allow_duplicate: bool = Form(False),
    db: Session = Depends(get_db),
    document_service: DocumentService = Depends(get_document_service),
    rag_resource: RAGResourceV2 = Depends(get_global_rag_resource),
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
            file=file.file,
            filename=file.filename,
            topic_id=topic_id,
            agent_id=None,
            db_session=db,
            build_index=False,
            use_original_filename=False,
        )

        # Perform normal extraction  (use_deep_extraction=False)
        result: ExtractionResponse = await deep_extract(
            DeepExtractionRequest(document_id=document.id, use_deep_extraction=False, config={}), db=db
        )

        await rag_resource.index_extraction_response(result, overwrite=False)
        pages = result.file_object.pages

        # Save normal extraction data
        await save_extraction_data(
            ExtractionDataRequest(
                original_filename=document.filename,
                source_document_id=document.id,
                extraction_results={
                    "original_filename": document.filename,
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
        task_id = await task_manager.add_deep_extract_task(
            document_id=document.id,
            data={
                "original_filename": document.original_filename,
                "extraction_date": datetime.now().isoformat(),
            },
        )

        logger.info(f"Document uploaded successfully with ID: {document.id}")
        return DocumentUploadResponse(success=True, document=document, message="Document uploaded successfully", task_id=task_id)

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
            remove_old_extraction_files=False,
            deep_extracted=False,
            metadata={},
        )

        logger.info(f"Successfully saved extraction JSON file with ID: {document.id}")
        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in save extraction data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=ExtractionOutput)
async def get_extraction_data(
    document_id: int,
    deep_extract: bool | None = None,
    db: Session = Depends(get_db),
    doc_repo: AbstractDocumentRepo = Depends(get_document_repo),
):
    """Get the extraction data for a document."""
    extraction = await doc_repo.get_extraction(document_id, deep_extract, db=db)
    if extraction is None:
        raise HTTPException(status_code=404, detail="Extraction data not found")
    return extraction
