"""Result key management for execution results."""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultKey:
    """Represents a unique identifier for any result in the execution hierarchy."""
    node_id: str  # e.g., "WORKFLOW_1", "ANALYZE_DATA", etc.
    step: str     # OODA step or None for non-OODA nodes
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def __str__(self) -> str:
        """String representation for storage and lookup."""
        return f"{self.node_id}.{self.step}"

    @classmethod
    def from_str(cls, key_str: str) -> 'ResultKey':
        """Create a ResultKey from its string representation."""
        node_id, step = key_str.split('.')
        return cls(node_id=node_id, step=step)

    @property
    def is_workflow(self) -> bool:
        """Check if this is a workflow-level result."""
        return self.node_id.startswith("WORKFLOW_")

    @property
    def is_plan(self) -> bool:
        """Check if this is a plan-level result."""
        return not self.is_workflow and "." not in self.node_id

    def is_current_plan(self) -> bool:
        """Check if this is part of the current plan execution."""
        # This will be set by the execution context
        return False  # Default implementation 