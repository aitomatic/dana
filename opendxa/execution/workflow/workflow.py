"""Workflow class for execution."""

from typing import List, Optional, Union

from ..execution_graph import ExecutionGraph
from ..execution_types import Objective, ExecutionSignal


class Workflow(ExecutionGraph):
    """Workflow graph for execution."""

    def __init__(self, objective: Optional[Union[str, Objective]] = None, name: Optional[str] = None):
        """Initialize workflow."""
        super().__init__(objective=objective, layer="workflow", name=name)
        self._cursor = None

    def update_from_signal(self, signal: ExecutionSignal) -> None:
        """Update workflow state from signal."""
        # For simple QA, no updates needed
        pass

    def process_signal(self, signal: ExecutionSignal) -> List[ExecutionSignal]:
        """Process signal and generate new signals."""
        return []  # For simple QA, no new signals needed

    def update_cursor(self, node_id: str) -> None:
        """Update workflow cursor to specified node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        self._cursor = self.get_a_cursor(self.nodes[node_id])

    def pretty_print(self) -> str:
        """Print workflow in a pretty format."""
        result = []
        result.append(f"Workflow: {self.name or 'Unnamed'}")
        result.append(f"Objective: {self._objective.current if self._objective else 'None'}")
        result.append("Nodes:")
        for node in self.nodes.values():
            result.append(f"  - {node.node_id}: {node.description[:50]}...")
        result.append("Edges:")
        for edge in self.edges:
            result.append(f"  - {edge.source} -> {edge.target}")
        return "\n".join(result)