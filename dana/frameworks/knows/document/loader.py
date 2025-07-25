"""
Document loading utilities.
"""

from typing import Any, Dict, List, Optional


class DocumentLoader:
    """Load documents from various sources."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the document loader."""
        self.config = config or {}
    
    def load(self, source: str) -> str:
        """Load document content from source."""
        # Placeholder implementation
        return f"Loaded content from {source}"
    
    def load_batch(self, sources: List[str]) -> List[str]:
        """Load multiple documents."""
        return [self.load(source) for source in sources] 