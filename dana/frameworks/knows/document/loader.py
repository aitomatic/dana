"""
Document loading utilities.
"""

from typing import Any


class DocumentLoader:
    """Load documents from various sources."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the document loader."""
        self.config = config or {}

    def load(self, source: str) -> str:
        """Load document content from source."""
        # Placeholder implementation
        return f"Loaded content from {source}"

    def load_batch(self, sources: list[str]) -> list[str]:
        """Load multiple documents."""
        return [self.load(source) for source in sources]
