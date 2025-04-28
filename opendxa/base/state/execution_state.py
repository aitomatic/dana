"""Execution state management for DXA."""

from typing import Dict, Any, Optional, List
from datetime import datetime
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
    """Manages execution state for a run.
    
    Tracks:
    - Current execution status
    - Current node being executed
    - Results from each node
    - Execution history
    - Visited nodes
    - Execution path
    """
    
    status: ExecutionStatus = Field(default=ExecutionStatus.IDLE)
    current_node_id: Optional[str] = Field(default=None)
    node_results: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    visited_nodes: List[str] = Field(default_factory=list)
    execution_path: List[tuple[str, str]] = Field(default_factory=list)
    
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
            
    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to execution history.
        
        Args:
            entry: Dictionary containing history information
        """
        entry['timestamp'] = datetime.now()
        self.history.append(entry)
        
    def reset(self) -> None:
        """Reset execution state to initial values."""
        self.status = ExecutionStatus.IDLE
        self.current_node_id = None
        self.node_results = {}
        self.history = []
        self.visited_nodes = []
        self.execution_path = []
        
    def get_node_result(self, node_id: str) -> Optional[Any]:
        """Get result for a specific node.
        
        Args:
            node_id: ID of the node to get result for
            
        Returns:
            The node's result or None if not found
        """
        return self.node_results.get(node_id)
        
    def get_execution_path(self) -> List[tuple[str, str]]:
        """Get the sequence of node transitions.
        
        Returns:
            List of (from_node, to_node) tuples
        """
        return self.execution_path
        
    def get_visited_nodes(self) -> List[str]:
        """Get list of visited nodes in order.
        
        Returns:
            List of node IDs in order of visitation
        """
        return self.visited_nodes
        
    def get_history(self) -> List[Dict[str, Any]]:
        """Get execution history.
        
        Returns:
            List of history entries
        """
        return self.history 