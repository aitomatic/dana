"""Result key management for execution results."""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultKey:
    """Represents a unique identifier for any result in the execution hierarchy."""
    node_id: str  # e.g., "DEFINE.ANALYZE_DATA" or "ANALYZE_DATA" for backward compatibility
    step: str     # OODA step or None for non-OODA nodes
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def __str__(self) -> str:
        """String representation for storage and lookup."""
        return f"{self.node_id}.{self.step}"

    @classmethod
    def from_str(cls, key_str: str) -> 'ResultKey':
        """Create a ResultKey from its string representation.
        
        The key_str should be in the format "node_id.step" where node_id can be:
        - A composite ID (e.g., "DEFINE.ANALYZE_DATA")
        - A simple ID (e.g., "ANALYZE_DATA") for backward compatibility
        """
        # Split on the last dot to separate node_id from step
        parts = key_str.rsplit('.', 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid key format: {key_str}. Expected 'node_id.step'"
            )
        node_id, step = parts
        return cls(node_id=node_id, step=step)

    @property
    def is_workflow(self) -> bool:
        """Check if this is a workflow-level result."""
        # For backward compatibility, check if it starts with WORKFLOW_
        if self.node_id.startswith("WORKFLOW_"):
            return True
        # For new format, check if it has a workflow prefix
        workflow_prefixes = ["DEFINE", "RESEARCH", "STRATEGIZE", "EXECUTE", "EVALUATE"]
        return '.' in self.node_id and self.node_id.split('.')[0] in workflow_prefixes

    @property
    def is_plan(self) -> bool:
        """Check if this is a plan-level result."""
        # For backward compatibility, check if it's not a workflow
        if not self.is_workflow:
            return '.' not in self.node_id
        # For new format, check if it's a composite ID
        return '.' in self.node_id

    def get_workflow_id(self) -> Optional[str]:
        """Get the workflow ID if this is a composite key."""
        if '.' in self.node_id:
            return self.node_id.split('.')[0]
        return None

    def get_plan_id(self) -> str:
        """Get the plan ID from the node_id."""
        if '.' in self.node_id:
            return self.node_id.split('.')[1]
        return self.node_id

    def is_current_plan(self) -> bool:
        """Check if this is part of the current plan execution."""
        # This will be set by the execution context
        return False  # Default implementation 