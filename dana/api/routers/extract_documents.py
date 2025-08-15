"""
Deep Document Extraction routers - routing for document extraction endpoints using aicapture.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.models import Document
from dana.api.core.schemas import DeepExtractionRequest, ExtractionResponse
from dana.api.services.deep_extraction_service import DeepExtractionService
from dana.api.services.llamaindex_extraction_service import LlamaIndexExtractionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract-documents", tags=["extract-documents"])


@router.post("/extract", response_model=ExtractionResponse)
async def deep_extract(request: DeepExtractionRequest, db: Session = Depends(get_db)):
    """
    Extract data from a visual document using aicapture.

    This endpoint supports various file types that aicapture can handle:
    - Images: PNG, JPG, JPEG, GIF, BMP, TIFF, TIF, WEBP
    - Documents: PDF

    Args:
        request: Extraction request containing document_id, prompt, and config
        db: Database session

    Returns:
        ExtractionResponse with extracted data
    """
    try:
        logger.info("Received deep extraction request for document ID: %s", request.document_id)

        # Get document from database
        document = db.query(Document).filter(Document.id == request.document_id).first()
        if not document:
            raise FileNotFoundError(f"Document not found with ID: {request.document_id}")

        if not document.file_path:
            raise FileNotFoundError(f"Document {request.document_id} has no file path")

        # Create service instance
        if request.use_deep_extraction:
            service = DeepExtractionService()
        else:
            service = LlamaIndexExtractionService()

        # Extract document - now just handles the extraction logic
        result = await service.extract(file_path=str(document.file_path), prompt=request.prompt, config=request.config)

        logger.info("Successfully extracted document ID: %s", request.document_id)
        return result

    except ImportError as e:
        logger.error(f"aicapture import error: {e}")
        raise HTTPException(status_code=503, detail="Document extraction service is not available. Please install aicapture package.")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in deep extraction endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract/supported-types")
async def get_supported_file_types():
    """
    Get list of supported file types for deep document extraction.

    Returns:
        Dictionary containing supported file extensions
    """
    try:
        service = DeepExtractionService()
        return {
            "supported_extensions": list(service.supported_extensions),
            "description": "File types supported for deep document extraction using aicapture",
            "note": "This endpoint requires aicapture package to be installed for actual processing",
        }
    except Exception as e:
        logger.error(f"Error getting supported file types: {e}")
        raise HTTPException(status_code=500, detail=str(e))
