"""Execution state management."""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import Field
from opendxa.base.state.base_state import BaseState

class ExecutionStatus(Enum):
    """Status of execution."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExecutionState(BaseState):
    """Manages execution state."""
    model_config = {"arbitrary_types_allowed": True}

    status: ExecutionStatus = Field(default=ExecutionStatus.IDLE, description="The status of the execution")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="The metadata of the execution")
    current_node_id: Optional[str] = Field(default=None, description="The current node ID of the execution")
    step_results: Dict[str, Any] = Field(default_factory=dict, description="The results of the execution steps")
    visited_nodes: List[str] = Field(default_factory=list, description="The nodes visited by the execution")
    node_results: Dict[str, Any] = Field(default_factory=dict, description="The results of the execution nodes")
    execution_path: List[tuple[str, str]] = Field(default_factory=list, description="The path of the execution")

    def __init__(self, **data: Any) -> None:
        """Initialize execution state."""
        super().__init__(**data)
        self.status = ExecutionStatus.IDLE
        self.step_results = {}
        self.visited_nodes = []
        self.node_results = {}
        self.execution_path = []

    def initialize(self) -> None:
        """Initialize execution state."""
        self.status = ExecutionStatus.IDLE

    def reset(self) -> None:
        """Reset execution state to initial values."""
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
                "result": self.node_results[node_id] if node_id in self.node_results else None
            }
            for node_id in self.visited_nodes
        ]
