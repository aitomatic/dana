"""Base edge implementation for graphs."""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Edge:
    """Base graph edge."""
    source: str  # Source node ID
    target: str  # Target node ID
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Make edge hashable by source/target pair."""
        return hash((self.source, self.target))

    def __eq__(self, other: object) -> bool:
        """Edges are equal if they have same source/target."""
        if not isinstance(other, Edge):
            return NotImplemented
        return self.source == other.source and self.target == other.target