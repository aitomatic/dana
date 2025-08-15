"""
Deep Extraction Service Module

This module provides business logic for visual document extraction and processing.
Supports various file types that aicapture can handle.
"""

import logging
import os
from pathlib import Path
from typing import Any

from dana.api.core.schemas import ExtractionResponse, FileObject, PageContent

logger = logging.getLogger(__name__)


class DeepExtractionService:
    """
    Service for handling visual document extraction operations using aicapture.
    """

    def __init__(self):
        """Initialize the deep extraction service."""
        # Only allow file types that aicapture can actually process (images and PDFs)
        self.supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".webp",  # Images
            ".pdf",  # PDFs
        }

    def is_supported_file_type(self, file_path: str) -> bool:
        """
        Check if the file type is supported for extraction.

        Args:
            file_path: Path to the file

        Returns:
            True if file type is supported, False otherwise
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_extensions

    def _get_vision_parser(self, config: dict | None = None):
        """Get a configured VisionParser instance."""
        try:
            from aicapture import VisionParser
            from aicapture.settings import MAX_CONCURRENT_TASKS, ImageQuality
            from aicapture.vision_parser import DEFAULT_PROMPT
        except ImportError:
            raise ImportError("aicapture package is not installed. Please install it to use deep extraction features.")

        if config is None:
            config = {}

        return VisionParser(
            vision_model=config.get("vision_model", None),
            cache_dir=config.get("cache_dir", None),
            max_concurrent_tasks=config.get("max_concurrent_tasks", MAX_CONCURRENT_TASKS),
            image_quality=config.get("image_quality", ImageQuality.DEFAULT),
            invalidate_cache=config.get("invalidate_cache", False),
            cloud_bucket=config.get("cloud_bucket", None),
            prompt=config.get("prompt", DEFAULT_PROMPT),
            dpi=config.get("dpi", 333),
        )

    async def _process_with_aicapture(self, file_path: str, prompt: str | None, config: dict | None = None) -> dict[str, Any]:
        """
        Process file using aicapture VisionParser.

        Args:
            file_path: Path to the file to process
            prompt: Custom prompt for processing
            config: Configuration dictionary for the processor

        Returns:
            Dict containing processing results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        # Handle PDF files
        if file_ext == ".pdf":
            parser = self._get_vision_parser(config)
            if prompt:
                parser.prompt = prompt
            return await parser.process_pdf_async(file_path)
        elif file_ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp", ".gif"]:
            parser = self._get_vision_parser(config)
            if prompt:
                parser.prompt = prompt
            return await parser.process_image_async(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported types: PDF, Images (jpg, jpeg, png, tiff, tif, webp, bmp, gif)")

    def _convert_aicapture_response(self, aicapture_result: dict[str, Any], file_path: str, prompt: str | None) -> ExtractionResponse:
        """
        Convert aicapture response to our API response format.

        Args:
            aicapture_result: Raw result from aicapture
            file_path: Original file path
            prompt: Original prompt used

        Returns:
            ExtractionResponse in our API format
        """
        file_name = Path(file_path).name
        file_full_path = os.path.abspath(file_path)

        # If the aicapture_result is already in the expected API format, just return it
        # (This can happen if aicapture_result is a dict with a "file_object" key)
        if (
            isinstance(aicapture_result, dict)
            and "file_object" in aicapture_result
            and isinstance(aicapture_result["file_object"], dict)
            and "pages" in aicapture_result["file_object"]
        ):
            file_obj = aicapture_result["file_object"]
            # Convert pages to PageContent objects if needed
            pages = [
                PageContent(
                    page_number=page.get("page_number", i + 1),
                    page_content=page.get("page_content", ""),
                    page_hash=page.get("page_hash", ""),
                )
                for i, page in enumerate(file_obj.get("pages", []))
            ]
            file_object = FileObject(
                file_name=file_obj.get("file_name", file_name),
                cache_key=file_obj.get("cache_key", ""),
                total_pages=file_obj.get("total_pages", len(pages)),
                total_words=file_obj.get("total_words", 0),
                file_full_path=file_obj.get("file_full_path", file_full_path),
                pages=pages,
            )
            return ExtractionResponse(file_object=file_object)

        # Otherwise, build the response from the raw aicapture_result
        pages = []
        total_words = 0

        if "pages" in aicapture_result and isinstance(aicapture_result["pages"], list):
            # PDF or multipage response
            for i, page_data in enumerate(aicapture_result["pages"]):
                page_content = page_data.get("content", "")
                page_number = page_data.get("page_number", i + 1)
                page_hash = page_data.get("page_hash", "")
                pages.append(PageContent(page_number=page_number, page_content=page_content, page_hash=page_hash))
            total_words = aicapture_result.get("total_words", 0)
        elif "content" in aicapture_result:
            # Single image response
            content = aicapture_result["content"]
            page_hash = aicapture_result.get("page_hash", "")
            pages.append(PageContent(page_number=1, page_content=content, page_hash=page_hash))
            total_words = aicapture_result.get("total_words", 0)
        else:
            # Fallback: treat the entire result as content (should rarely happen)
            content = str(aicapture_result)
            page_hash = aicapture_result.get("page_hash", "")
            pages.append(PageContent(page_number=1, page_content=content, page_hash=page_hash))
            total_words = aicapture_result.get("total_words", 0)

        cache_key = aicapture_result.get("cache_key", "")

        file_object = FileObject(
            file_name=file_name,
            cache_key=cache_key,
            total_pages=len(pages),
            total_words=total_words,
            file_full_path=file_full_path,
            pages=pages,
        )

        return ExtractionResponse(file_object=file_object)

    async def extract(self, file_path: str, prompt: str | None = None, config: dict | None = None) -> ExtractionResponse:
        """
        Extract data from a visual document using aicapture.

        Args:
            file_path: Path to the file to process
            prompt: Optional custom prompt for processing
            config: Optional configuration dictionary for the processor

        Returns:
            ExtractionResponse with extracted data
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check if file type is supported
            if not self.is_supported_file_type(file_path):
                raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")

            logger.info("Processing file with aicapture: %s", file_path)

            # Process with aicapture
            aicapture_result = await self._process_with_aicapture(file_path, prompt, config or {})

            # Convert to our API response format
            result = self._convert_aicapture_response(aicapture_result, file_path, prompt)

            logger.info("Successfully processed file: %s", file_path)
            return result

        except ImportError as e:
            logger.error(f"aicapture import error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting visual document: {e}")
            raise
