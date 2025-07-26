"""
Document parsing utilities.
"""

from typing import Any


class DocumentParser:
    """Parse documents into structured formats."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the document parser."""
        self.config = config or {}

    def parse(self, content: str) -> dict[str, Any]:
        """Parse document content."""
        return {"content": content, "parsed": True, "metadata": {"length": len(content)}}

    def parse_batch(self, contents: list[str]) -> list[dict[str, Any]]:
        """Parse multiple documents."""
        return [self.parse(content) for content in contents]
