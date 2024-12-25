"""Base node definition for directed graphs."""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

@dataclass
class Node:
    """Base class for graph nodes."""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.node_id)
