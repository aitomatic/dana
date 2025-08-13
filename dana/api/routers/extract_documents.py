"""
Deep Document Extraction routers - routing for document extraction endpoints using aicapture.
"""

import logging

from fastapi import APIRouter, HTTPException

from dana.api.core.schemas import DeepExtractionRequest, DeepExtractionResponse
from dana.api.services.deep_extraction_service import DeepExtractionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract-documents", tags=["extract-documents"])


@router.post("/deep-extract", response_model=DeepExtractionResponse)
async def deep_extract(request: DeepExtractionRequest):
    """
    Extract data from a visual document using aicapture.

    This endpoint supports various file types that aicapture can handle:
    - Images: PNG, JPG, JPEG, GIF, BMP, TIFF, TIF, WEBP
    - Documents: PDF

    Args:
        request: Extraction request containing file_path, prompt, and config

    Returns:
        DeepExtractionResponse with extracted data
    """
    try:
        logger.info(f"Received deep extraction request: {request.file_path}")

        # Create service instance
        service = DeepExtractionService()

        # Extract document
        result = await service.deep_extract(request)

        logger.info(f"Successfully extracted document: {request.file_path}")
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


@router.get("/deep-extract/supported-types")
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
