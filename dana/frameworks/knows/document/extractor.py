"""
Text extraction utilities for document processing.
"""

from typing import Any


class TextExtractor:
    """Extract text content from various document formats."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the text extractor."""
        self.config = config or {}

    def extract_text(self, content: str) -> str:
        """Extract text from content."""
        return content.strip()

    def extract_metadata(self, content: str) -> dict[str, Any]:
        """Extract metadata from content."""
        return {"length": len(content), "type": "text"}
