"""
LlamaIndex Extraction Service Module

This module provides business logic for document extraction and processing using llamaIndex.
Supports various file types that llamaIndex can handle.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

from dana.api.core.schemas import ExtractionResponse, FileObject, PageContent

logger = logging.getLogger(__name__)


class LlamaIndexExtractionService:
    """
    Service for handling document extraction operations using llamaIndex.
    """

    def __init__(self):
        """Initialize the llamaIndex extraction service."""
        # Supported file types for llamaIndex
        self.supported_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
            ".csv",  # Text files
            ".pdf",  # PDFs
            ".docx",
            ".doc",  # Word documents
            ".pptx",
            ".ppt",  # PowerPoint
            ".xlsx",
            ".xls",  # Excel
            ".rtf",  # Rich text
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

    def _get_llamaindex_reader(self, config: dict | None = None):
        """Get a configured llamaIndex reader instance."""
        try:
            from llama_index.core.readers.file.base import SimpleDirectoryReader
            from llama_index.core.readers.file.docs_reader import PDFReader
            from llama_index.core.readers.file.docx_reader import DocxReader
            from llama_index.core.readers.file.epub_reader import EpubReader
            from llama_index.core.readers.file.markdown_reader import MarkdownReader
            from llama_index.core.readers.file.mbox_reader import MboxReader
            from llama_index.core.readers.file.paged_csv_reader import PagedCSVReader
            from llama_index.core.readers.file.pymu_pdf_reader import PyMuPDFReader
            from llama_index.core.readers.file.rtf_reader import RTFReader
            from llama_index.core.readers.file.tabular_reader import CSVReader
            from llama_index.core.readers.file.xml_reader import XMLReader
        except ImportError:
            raise ImportError("llamaIndex package is not installed. Please install it to use extraction features.")

        if config is None:
            config = {}

        # Configure file extractors based on config
        file_extractors = config.get("file_extractors", {})

        return {"reader": SimpleDirectoryReader, "file_extractors": file_extractors}

    async def _process_with_llamaindex(self, file_path: str, prompt: str | None, config: dict | None = None) -> dict[str, Any]:
        """
        Process file using llamaIndex.

        Args:
            file_path: Path to the file to process
            prompt: Custom prompt for processing (not used in basic extraction)
            config: Configuration dictionary for the processor

        Returns:
            Dict containing processing results
        """
        logger.info("_process_with_llamaindex received file_path: '%s'", file_path)
        logger.info("_process_with_llamaindex file_path exists: %s", os.path.exists(file_path))

        try:
            from llama_index.core.readers.file.base import SimpleDirectoryReader

            # file_path should already be absolute from the extract method
            filename = os.path.basename(file_path)

            logger.info("Processing file: '%s' with full path: '%s'", filename, file_path)

            # Use the full file path directly
            logger.info("Creating SimpleDirectoryReader with input_files: %s", [file_path])
            reader = SimpleDirectoryReader(input_files=[file_path], recursive=False, encoding="utf-8", errors="ignore")

            # Load documents
            logger.info("Loading documents with llamaIndex...")
            documents = reader.load_data()
            logger.info("Loaded %d documents", len(documents))

            if not documents:
                raise ValueError(f"No content could be extracted from {file_path}")

            # Process documents and extract text
            extracted_content = []
            total_words = 0

            for i, doc in enumerate(documents):
                content = doc.text
                extracted_content.append(
                    {"page_number": i + 1, "page_content": content, "page_hash": hashlib.md5(content.encode()).hexdigest()}
                )
                total_words += len(content.split())

            return {
                "file_name": filename,
                "cache_key": hashlib.md5(file_path.encode()).hexdigest(),
                "total_pages": len(extracted_content),
                "total_words": total_words,
                "file_full_path": file_path,  # Use absolute path like DeepExtractionService
                "pages": extracted_content,
            }

        except Exception as e:
            logger.error(f"Error processing file with llamaIndex: {e}")
            raise ValueError(f"Failed to extract content from file: {str(e)}")

    async def extract(self, file_path: str, prompt: str | None = None, config: dict | None = None) -> ExtractionResponse:
        """
        Extract data from a document using llamaIndex.

        Args:
            file_path: Path to the file to extract
            prompt: Custom prompt for processing (not used in basic extraction)
            config: Configuration dictionary for the processor

        Returns:
            ExtractionResponse with extracted data
        """
        try:
            # Resolve to absolute path first
            abs_file_path = os.path.abspath(file_path)

            # Validate file exists with absolute path
            if not os.path.exists(abs_file_path):
                raise FileNotFoundError(f"File {os.path.basename(file_path)} does not exist.")

            # Check if file type is supported
            if not self.is_supported_file_type(abs_file_path):
                raise ValueError(f"Unsupported file type: {Path(abs_file_path).suffix}")

            logger.info("Processing file with llamaIndex: %s", abs_file_path)

            # Process the file
            result = await self._process_with_llamaindex(abs_file_path, prompt, config or {})

            # Create response
            pages = [
                PageContent(page_number=page["page_number"], page_content=page["page_content"], page_hash=page["page_hash"])
                for page in result["pages"]
            ]

            file_object = FileObject(
                file_name=result["file_name"],
                cache_key=result["cache_key"],
                total_pages=result["total_pages"],
                total_words=result["total_words"],
                file_full_path=result["file_full_path"],
                pages=pages,
            )

            logger.info("Successfully processed file: %s", abs_file_path)
            return ExtractionResponse(file_object=file_object)

        except ImportError as e:
            logger.error(f"llamaIndex import error: {e}")
            raise
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting document: {e}")
            raise
