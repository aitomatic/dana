"""
Document parser for Dana KNOWS system.

This module handles parsing different document formats and extracting structured data.
"""

import json
import re
from typing import Any

from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.knows.core.base import Document, ParsedDocument, ProcessorBase


class DocumentParser(ProcessorBase):
    """Parse documents into structured format."""
    
    def __init__(self):
        """Initialize document parser."""
        DANA_LOGGER.info("Initialized DocumentParser")
    
    def process(self, document: Document) -> ParsedDocument:
        """Parse document into structured format.
        
        Args:
            document: Document to parse
            
        Returns:
            ParsedDocument with structured data
            
        Raises:
            ValueError: If document format not supported
        """
        if not self.validate_input(document):
            raise ValueError("Invalid document provided for parsing")
        
        try:
            # Parse based on document format
            if document.format in ["txt", "md"]:
                structured_data = self._parse_text_document(document)
            elif document.format == "json":
                structured_data = self._parse_json_document(document)
            elif document.format == "csv":
                structured_data = self._parse_csv_document(document)
            else:
                # Fallback to basic parsing
                structured_data = self._parse_generic_document(document)
            
            parsed_doc = ParsedDocument(
                document=document,
                text_content=document.content,
                structured_data=structured_data,
                metadata={
                    "parser_version": "1.0",
                    "parsed_elements": len(structured_data),
                    "format": document.format
                }
            )
            
            DANA_LOGGER.info(f"Successfully parsed document {document.id} (format: {document.format})")
            return parsed_doc
            
        except Exception as e:
            DANA_LOGGER.error(f"Failed to parse document {document.id}: {str(e)}")
            raise ValueError(f"Document parsing failed: {str(e)}")
    
    def validate_input(self, document: Document) -> bool:
        """Validate document before parsing.
        
        Args:
            document: Document to validate
            
        Returns:
            True if document is valid for parsing
        """
        if not isinstance(document, Document):
            DANA_LOGGER.error("Input must be a Document object")
            return False
        
        if not document.content:
            DANA_LOGGER.error("Document content is empty")
            return False
        
        if not document.format:
            DANA_LOGGER.error("Document format not specified")
            return False
        
        return True
    
    def _parse_text_document(self, document: Document) -> dict[str, Any]:
        """Parse text or markdown document.
        
        Args:
            document: Text document to parse
            
        Returns:
            Structured data extracted from text
        """
        content = document.content
        structured_data = {
            "type": "text_document",
            "sections": [],
            "headers": [],
            "lists": [],
            "metadata": {}
        }
        
        # Extract headers (markdown style)
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        for level_marks, title in headers:
            structured_data["headers"].append({
                "level": len(level_marks),
                "title": title.strip(),
                "type": "header"
            })
        
        # Split into sections based on headers
        if structured_data["headers"]:
            sections = re.split(r'^#{1,6}\s+.+$', content, flags=re.MULTILINE)
            for i, section in enumerate(sections[1:]):  # Skip first empty section
                if section.strip():
                    structured_data["sections"].append({
                        "index": i,
                        "content": section.strip(),
                        "type": "section"
                    })
        else:
            # No headers found, treat as single section
            structured_data["sections"].append({
                "index": 0,
                "content": content.strip(),
                "type": "section"
            })
        
        # Extract lists
        list_items = re.findall(r'^[-*+]\s+(.+)$', content, re.MULTILINE)
        numbered_items = re.findall(r'^\d+\.\s+(.+)$', content, re.MULTILINE)
        
        if list_items:
            structured_data["lists"].append({
                "type": "unordered",
                "items": list_items
            })
        
        if numbered_items:
            structured_data["lists"].append({
                "type": "ordered", 
                "items": numbered_items
            })
        
        # Extract metadata
        structured_data["metadata"] = {
            "word_count": len(content.split()),
            "line_count": len(content.splitlines()),
            "char_count": len(content),
            "has_headers": len(structured_data["headers"]) > 0,
            "has_lists": len(structured_data["lists"]) > 0
        }
        
        return structured_data
    
    def _parse_json_document(self, document: Document) -> dict[str, Any]:
        """Parse JSON document.
        
        Args:
            document: JSON document to parse
            
        Returns:
            Structured data from JSON
        """
        try:
            json_data = json.loads(document.content)
            
            structured_data = {
                "type": "json_document",
                "data": json_data,
                "schema": self._analyze_json_schema(json_data),
                "metadata": {
                    "is_array": isinstance(json_data, list),
                    "is_object": isinstance(json_data, dict),
                    "keys": list(json_data.keys()) if isinstance(json_data, dict) else [],
                    "length": len(json_data) if isinstance(json_data, (list, dict)) else 0
                }
            }
            
            return structured_data
            
        except json.JSONDecodeError as e:
            DANA_LOGGER.error(f"Invalid JSON in document {document.id}: {str(e)}")
            return self._parse_generic_document(document)
    
    def _parse_csv_document(self, document: Document) -> dict[str, Any]:
        """Parse CSV document.
        
        Args:
            document: CSV document to parse
            
        Returns:
            Structured data from CSV
        """
        lines = document.content.strip().split('\n')
        
        if not lines:
            return self._parse_generic_document(document)
        
        # Assume first line is header
        headers = [col.strip() for col in lines[0].split(',')]
        rows = []
        
        for line in lines[1:]:
            if line.strip():
                row_data = [col.strip() for col in line.split(',')]
                if len(row_data) == len(headers):
                    rows.append(dict(zip(headers, row_data, strict=False)))
        
        structured_data = {
            "type": "csv_document",
            "headers": headers,
            "rows": rows,
            "metadata": {
                "column_count": len(headers),
                "row_count": len(rows),
                "total_lines": len(lines)
            }
        }
        
        return structured_data
    
    def _parse_generic_document(self, document: Document) -> dict[str, Any]:
        """Parse document with generic approach.
        
        Args:
            document: Document to parse
            
        Returns:
            Basic structured data
        """
        content = document.content
        
        structured_data = {
            "type": "generic_document",
            "content": content,
            "metadata": {
                "word_count": len(content.split()),
                "line_count": len(content.splitlines()),
                "char_count": len(content),
                "format": document.format
            }
        }
        
        return structured_data
    
    def _analyze_json_schema(self, data: Any, path: str = "") -> dict[str, Any]:
        """Analyze JSON data structure to create schema information.
        
        Args:
            data: JSON data to analyze
            path: Current path in the data structure
            
        Returns:
            Schema information
        """
        if isinstance(data, dict):
            schema = {
                "type": "object",
                "properties": {},
                "path": path
            }
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                schema["properties"][key] = self._analyze_json_schema(value, new_path)
            return schema
        
        elif isinstance(data, list):
            schema = {
                "type": "array",
                "length": len(data),
                "path": path
            }
            if data:
                # Analyze first item as representative
                schema["items"] = self._analyze_json_schema(data[0], f"{path}[0]")
            return schema
        
        else:
            return {
                "type": type(data).__name__,
                "value": str(data) if len(str(data)) < 100 else str(data)[:100] + "...",
                "path": path
            } 