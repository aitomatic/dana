"""Execution state tracking."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from opendxa.base.state.base_state import BaseState

class ExecutionStatus(Enum):
    """Status of execution state."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class ExecutionState(BaseState):
    """Tracks execution progress including graph position.
    
    Attributes:
        status: Current execution status
        current_step: ID of the current step being executed
        step_results: Results from each step execution
        current_node_id: ID of the current node in the execution graph
        visited_nodes: List of node IDs that have been visited
        node_results: Results from each node execution
        execution_path: List of tuples representing the path taken (from_node, to_node)
    """
    
    # General execution state
    status: ExecutionStatus = ExecutionStatus.IDLE
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    
    # Graph progress tracking
    current_node_id: Optional[str] = None
    visited_nodes: List[str] = field(default_factory=list)
    node_results: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[Tuple[str, str]] = field(default_factory=list)  # (from_node, to_node)

    def initialize(self) -> None:
        """Initialize execution state to default values."""
        super().initialize()
        self.status = ExecutionStatus.IDLE
        self.current_step = None
        self.current_node_id = None
        self.initialized = True

    def reset(self) -> None:
        """Reset execution state to initial values."""
        super().reset()
        self.step_results.clear()
        self.visited_nodes.clear()
        self.node_results.clear()
        self.execution_path.clear()

    def update_node(self, node_id: str, result: Optional[Any] = None) -> None:
        """Update current node and record result.
        
        Args:
            node_id: ID of the node to update to
            result: Optional result from the node execution
        """
        if self.current_node_id:
            self.execution_path.append((self.current_node_id, node_id))
        self.current_node_id = node_id
        self.visited_nodes.append(node_id)
        if result is not None:
            self.node_results[node_id] = result

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history with results.
        
        Returns:
            List of dictionaries containing node IDs and their results
        """
        return [
            {
                "node_id": node_id,
                "result": self.node_results.get(node_id)
            }
            for node_id in self.visited_nodes
        ]
