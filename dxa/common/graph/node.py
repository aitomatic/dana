"""Base node implementation for graphs."""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Node:
    """Base graph node."""
    node_id: str
    type: str = "node"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make node hashable by id."""
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        """Nodes are equal if they have the same id."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.node_id == other.node_id
