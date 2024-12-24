"""Base node definition for directed graphs."""

from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class Node:
    """Base class for graph nodes."""
    node_id: str
    type: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.node_id)
