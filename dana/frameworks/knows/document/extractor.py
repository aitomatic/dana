"""
Text extractor for Dana KNOWS system.

This module handles extracting clean, structured text from parsed documents.
"""

import re
from typing import Any

from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import ParsedDocument, ProcessorBase


class TextExtractor(ProcessorBase):
    """Extract clean text from parsed documents."""
    
    def __init__(self, 
                 preserve_structure: bool = True,
                 include_metadata: bool = True,
                 max_text_length: int | None = None):
        """Initialize text extractor.
        
        Args:
            preserve_structure: Whether to preserve document structure in output
            include_metadata: Whether to include metadata in extraction
            max_text_length: Maximum length of extracted text (optional)
        """
        self.preserve_structure = preserve_structure
        self.include_metadata = include_metadata
        self.max_text_length = max_text_length
        DANA_LOGGER.info(f"Initialized TextExtractor (structure: {preserve_structure}, metadata: {include_metadata})")
    
    def process(self, parsed_doc: ParsedDocument) -> str:
        """Extract clean text from parsed document.
        
        Args:
            parsed_doc: ParsedDocument to extract text from
            
        Returns:
            Clean extracted text
            
        Raises:
            ValueError: If parsed document is invalid
        """
        if not self.validate_input(parsed_doc):
            raise ValueError("Invalid parsed document provided for text extraction")
        
        try:
            # Extract text based on document type
            if parsed_doc.structured_data.get("type") == "text_document":
                extracted_text = self._extract_from_text_document(parsed_doc)
            elif parsed_doc.structured_data.get("type") == "json_document":
                extracted_text = self._extract_from_json_document(parsed_doc)
            elif parsed_doc.structured_data.get("type") == "csv_document":
                extracted_text = self._extract_from_csv_document(parsed_doc)
            else:
                # Fallback to generic extraction
                extracted_text = self._extract_generic_text(parsed_doc)
            
            # Apply length limit if specified
            if self.max_text_length and len(extracted_text) > self.max_text_length:
                extracted_text = extracted_text[:self.max_text_length] + "..."
                DANA_LOGGER.info(f"Truncated text to {self.max_text_length} characters")
            
            DANA_LOGGER.info(f"Successfully extracted text from document {parsed_doc.document.id} ({len(extracted_text)} chars)")
            return extracted_text
            
        except Exception as e:
            DANA_LOGGER.error(f"Failed to extract text from document {parsed_doc.document.id}: {str(e)}")
            raise ValueError(f"Text extraction failed: {str(e)}")
    
    def validate_input(self, parsed_doc: ParsedDocument) -> bool:
        """Validate parsed document before text extraction.
        
        Args:
            parsed_doc: ParsedDocument to validate
            
        Returns:
            True if document is valid for extraction
        """
        if not isinstance(parsed_doc, ParsedDocument):
            DANA_LOGGER.error("Input must be a ParsedDocument object")
            return False
        
        if not parsed_doc.text_content:
            DANA_LOGGER.error("ParsedDocument has no text content")
            return False
        
        if not parsed_doc.structured_data:
            DANA_LOGGER.error("ParsedDocument has no structured data")
            return False
        
        return True
    
    def _extract_from_text_document(self, parsed_doc: ParsedDocument) -> str:
        """Extract text from text/markdown document.
        
        Args:
            parsed_doc: ParsedDocument with text document data
            
        Returns:
            Extracted and formatted text
        """
        structured_data = parsed_doc.structured_data
        extracted_parts = []
        
        if self.preserve_structure:
            # Extract with structure preservation
            if structured_data.get("headers"):
                # Process sections with headers
                for i, header in enumerate(structured_data["headers"]):
                    # Add header
                    level_prefix = "#" * header["level"]
                    extracted_parts.append(f"{level_prefix} {header['title']}")
                    
                    # Add corresponding section content if available
                    if i < len(structured_data.get("sections", [])):
                        section = structured_data["sections"][i]
                        extracted_parts.append(section["content"])
                    
                    extracted_parts.append("")  # Add spacing
            else:
                # No headers, just add sections
                for section in structured_data.get("sections", []):
                    extracted_parts.append(section["content"])
                    extracted_parts.append("")
            
            # Add lists with formatting
            for list_item in structured_data.get("lists", []):
                if list_item["type"] == "ordered":
                    for i, item in enumerate(list_item["items"], 1):
                        extracted_parts.append(f"{i}. {item}")
                else:
                    for item in list_item["items"]:
                        extracted_parts.append(f"• {item}")
                extracted_parts.append("")
        else:
            # Simple text extraction without structure
            for section in structured_data.get("sections", []):
                extracted_parts.append(section["content"])
        
        # Add metadata if requested
        if self.include_metadata:
            metadata = structured_data.get("metadata", {})
            metadata_text = self._format_metadata(metadata)
            if metadata_text:
                extracted_parts.append("---")
                extracted_parts.append(metadata_text)
        
        return "\n".join(extracted_parts).strip()
    
    def _extract_from_json_document(self, parsed_doc: ParsedDocument) -> str:
        """Extract text from JSON document.
        
        Args:
            parsed_doc: ParsedDocument with JSON document data
            
        Returns:
            Extracted text representation of JSON
        """
        structured_data = parsed_doc.structured_data
        json_data = structured_data.get("data", {})
        
        extracted_parts = []
        
        if self.preserve_structure:
            # Create structured text representation
            extracted_parts.append("JSON Document Structure:")
            extracted_parts.append("")
            extracted_parts.extend(self._json_to_text(json_data))
        else:
            # Simple string representation
            extracted_parts.append(str(json_data))
        
        # Add metadata if requested
        if self.include_metadata:
            metadata = structured_data.get("metadata", {})
            metadata_text = self._format_metadata(metadata)
            if metadata_text:
                extracted_parts.append("---")
                extracted_parts.append(metadata_text)
        
        return "\n".join(extracted_parts).strip()
    
    def _extract_from_csv_document(self, parsed_doc: ParsedDocument) -> str:
        """Extract text from CSV document.
        
        Args:
            parsed_doc: ParsedDocument with CSV document data
            
        Returns:
            Extracted text representation of CSV
        """
        structured_data = parsed_doc.structured_data
        headers = structured_data.get("headers", [])
        rows = structured_data.get("rows", [])
        
        extracted_parts = []
        
        if self.preserve_structure:
            # Create table-like text representation
            extracted_parts.append("CSV Data:")
            extracted_parts.append("")
            
            if headers:
                extracted_parts.append("Headers: " + ", ".join(headers))
                extracted_parts.append("")
            
            for i, row in enumerate(rows):
                row_text = f"Row {i+1}: "
                row_items = []
                for header in headers:
                    value = row.get(header, "")
                    row_items.append(f"{header}: {value}")
                row_text += ", ".join(row_items)
                extracted_parts.append(row_text)
        else:
            # Simple concatenation
            for row in rows:
                extracted_parts.append(str(row))
        
        # Add metadata if requested
        if self.include_metadata:
            metadata = structured_data.get("metadata", {})
            metadata_text = self._format_metadata(metadata)
            if metadata_text:
                extracted_parts.append("---")
                extracted_parts.append(metadata_text)
        
        return "\n".join(extracted_parts).strip()
    
    def _extract_generic_text(self, parsed_doc: ParsedDocument) -> str:
        """Extract text using generic approach.
        
        Args:
            parsed_doc: ParsedDocument with generic structure
            
        Returns:
            Clean extracted text
        """
        # Start with the text content
        text = parsed_doc.text_content
        
        # Clean up the text
        text = self._clean_text(text)
        
        # Add metadata if requested
        if self.include_metadata:
            metadata = parsed_doc.structured_data.get("metadata", {})
            metadata_text = self._format_metadata(metadata)
            if metadata_text:
                text += f"\n---\n{metadata_text}"
        
        return text
    
    def _json_to_text(self, data: Any, indent: int = 0) -> list[str]:
        """Convert JSON data to readable text format.
        
        Args:
            data: JSON data to convert
            indent: Indentation level
            
        Returns:
            List of text lines
        """
        lines = []
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(self._json_to_text(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.extend(self._json_to_text(item, indent + 1))
                else:
                    lines.append(f"{prefix}[{i}]: {item}")
        else:
            lines.append(f"{prefix}{data}")
        
        return lines
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text
    
    def _format_metadata(self, metadata: dict[str, Any]) -> str:
        """Format metadata for text inclusion.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted metadata text
        """
        if not metadata:
            return ""
        
        metadata_lines = ["Document Metadata:"]
        for key, value in metadata.items():
            metadata_lines.append(f"  {key}: {value}")
        
        return "\n".join(metadata_lines) 