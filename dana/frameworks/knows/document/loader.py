"""
Document loader for Dana KNOWS system.

This module handles loading documents from various sources and formats.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import Document, DocumentBase


class DocumentLoader(DocumentBase):
    """Load documents from various sources."""
    
    SUPPORTED_FORMATS = ["txt", "md", "pdf", "json", "csv"]
    MAX_FILE_SIZE = 10485760  # 10MB
    
    def __init__(self, max_size: int | None = None):
        """Initialize document loader.
        
        Args:
            max_size: Maximum file size in bytes (optional)
        """
        self.max_size = max_size or self.MAX_FILE_SIZE
        DANA_LOGGER.info(f"Initialized DocumentLoader with max_size: {self.max_size} bytes")
    
    def load_document(self, source: str) -> Document:
        """Load document from file path.
        
        Args:
            source: File path to the document
            
        Returns:
            Document object with loaded content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format not supported or file too large
            IOError: If file cannot be read
        """
        if not os.path.exists(source):
            raise FileNotFoundError(f"Document file not found: {source}")
        
        # Check file size
        file_size = os.path.getsize(source)
        if file_size > self.max_size:
            raise ValueError(f"File too large: {file_size} bytes (max: {self.max_size} bytes)")
        
        # Determine format from extension
        file_path = Path(source)
        format_ext = file_path.suffix.lower().lstrip('.')
        
        if format_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {format_ext}. Supported: {self.SUPPORTED_FORMATS}")
        
        try:
            # Load content based on format
            content = self._load_content(source, format_ext)
            
            # Create document object
            document = Document(
                id=self._generate_document_id(source),
                source=source,
                content=content,
                format=format_ext,
                metadata={
                    "file_size": file_size,
                    "file_name": file_path.name,
                    "file_extension": format_ext,
                    "encoding": "utf-8"
                },
                created_at=datetime.now()
            )
            
            DANA_LOGGER.info(f"Successfully loaded document: {source} (format: {format_ext}, size: {file_size} bytes)")
            return document
            
        except Exception as e:
            DANA_LOGGER.error(f"Failed to load document from {source}: {str(e)}")
            raise OSError(f"Failed to read document: {str(e)}")
    
    def load_documents(self, sources: list[str]) -> list[Document]:
        """Load multiple documents from file paths.
        
        Args:
            sources: List of file paths
            
        Returns:
            List of Document objects
        """
        documents = []
        errors = []
        
        for source in sources:
            try:
                document = self.load_document(source)
                documents.append(document)
            except Exception as e:
                error_msg = f"Failed to load {source}: {str(e)}"
                errors.append(error_msg)
                DANA_LOGGER.warning(error_msg)
        
        if errors:
            DANA_LOGGER.warning(f"Failed to load {len(errors)} out of {len(sources)} documents")
        
        DANA_LOGGER.info(f"Successfully loaded {len(documents)} out of {len(sources)} documents")
        return documents
    
    def validate_document(self, document: Document) -> bool:
        """Validate document format and content.
        
        Args:
            document: Document to validate
            
        Returns:
            True if document is valid
        """
        try:
            # Check required fields
            if not document.id:
                DANA_LOGGER.error("Document validation failed: missing ID")
                return False
            
            if not document.content:
                DANA_LOGGER.error("Document validation failed: empty content")
                return False
            
            if document.format not in self.SUPPORTED_FORMATS:
                DANA_LOGGER.error(f"Document validation failed: unsupported format {document.format}")
                return False
            
            # Check content is string
            if not isinstance(document.content, str):
                DANA_LOGGER.error("Document validation failed: content must be string")
                return False
            
            DANA_LOGGER.info(f"Document validation passed: {document.id}")
            return True
            
        except Exception as e:
            DANA_LOGGER.error(f"Document validation error: {str(e)}")
            return False
    
    def _load_content(self, source: str, format_ext: str) -> str:
        """Load content from file based on format.
        
        Args:
            source: File path
            format_ext: File format extension
            
        Returns:
            File content as string
        """
        if format_ext in ["txt", "md"]:
            return self._load_text_file(source)
        elif format_ext == "json":
            return self._load_json_file(source)
        elif format_ext == "csv":
            return self._load_csv_file(source)
        elif format_ext == "pdf":
            return self._load_pdf_file(source)
        else:
            raise ValueError(f"Format handler not implemented: {format_ext}")
    
    def _load_text_file(self, source: str) -> str:
        """Load plain text or markdown file."""
        with open(source, encoding='utf-8') as f:
            return f.read()
    
    def _load_json_file(self, source: str) -> str:
        """Load JSON file and return as formatted string."""
        with open(source, encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=2)
    
    def _load_csv_file(self, source: str) -> str:
        """Load CSV file and return as string."""
        with open(source, encoding='utf-8') as f:
            return f.read()
    
    def _load_pdf_file(self, source: str) -> str:
        """Load PDF file using pdfplumber for text extraction."""
        try:
            import logging
            import warnings

            import pdfplumber
            
            # Suppress pdfminer warnings that are common with complex PDFs
            pdfminer_logger = logging.getLogger('pdfminer')
            original_level = pdfminer_logger.level
            pdfminer_logger.setLevel(logging.ERROR)
            
            # Suppress pdfplumber warnings
            warnings.filterwarnings('ignore', category=UserWarning, module='pdfplumber')
            
            try:
                DANA_LOGGER.info(f"Processing PDF file: {source}")
                text_content = ""
                page_count = 0
                successful_pages = 0
                
                with pdfplumber.open(source) as pdf:
                    page_count = len(pdf.pages)
                    DANA_LOGGER.info(f"PDF has {page_count} pages")
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                # Add page separator for multi-page documents (only if we have content)
                                if text_content and successful_pages > 0:
                                    text_content += f"\n\n--- Page {page_num} ---\n\n"
                                text_content += page_text.strip()
                                successful_pages += 1
                            else:
                                DANA_LOGGER.debug(f"No text found on page {page_num}")
                        except Exception as e:
                            DANA_LOGGER.warning(f"Failed to extract text from page {page_num}: {str(e)}")
                            continue
                
                if not text_content.strip():
                    DANA_LOGGER.warning(f"No text content extracted from PDF: {source}")
                    return f"[PDF file processed but no text content found: {source}]"
                
                DANA_LOGGER.info(f"Successfully extracted {len(text_content)} characters from {successful_pages}/{page_count} pages")
                return text_content.strip()
                
            finally:
                # Restore original logging level
                pdfminer_logger.setLevel(original_level)
                
        except ImportError:
            DANA_LOGGER.error("pdfplumber not installed - cannot process PDF files")
            raise OSError("PDF processing requires pdfplumber library. Install with: pip install pdfplumber")
        except Exception as e:
            DANA_LOGGER.error(f"Failed to process PDF file {source}: {str(e)}")
            raise OSError(f"PDF processing failed: {str(e)}")
    
    def _generate_document_id(self, source: str) -> str:
        """Generate unique document ID from source path.
        
        Args:
            source: Source file path
            
        Returns:
            Unique document ID
        """
        # Use file path hash for reproducible IDs
        import hashlib
        hash_input = f"{source}_{os.path.getmtime(source)}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"doc_{file_hash}" 