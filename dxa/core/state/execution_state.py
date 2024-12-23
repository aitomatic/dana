"""Execution state tracking."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from .base_state import BaseState

@dataclass
class ExecutionState(BaseState):
    """Tracks execution progress including graph position."""
    
    # General execution state
    status: str = "IDLE"
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    
    # Graph progress tracking
    current_node_id: Optional[str] = None
    visited_nodes: List[str] = field(default_factory=list)
    node_results: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[Tuple[str, str]] = field(default_factory=list)  # (from_node, to_node)

    def update_node(self, node_id: str, result: Any = None) -> None:
        """Update current node and record result."""
        if self.current_node_id:
            self.execution_path.append((self.current_node_id, node_id))
        self.current_node_id = node_id
        self.visited_nodes.append(node_id)
        if result is not None:
            self.node_results[node_id] = result

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history with results."""
        return [
            {
                "node_id": node_id,
                "result": self.node_results.get(node_id)
            }
            for node_id in self.visited_nodes
        ]
