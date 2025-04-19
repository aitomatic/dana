"""Plan implementation for concrete execution steps."""

from typing import List, Optional

from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.base.execution.execution_types import Objective, ExecutionNode, ObjectiveStatus, ExecutionSignal

class Plan(ExecutionGraph):
    """Concrete execution steps (WHAT layer)."""

    def __init__(self, objective: Optional[Objective] = None, name: Optional[str] = None):
        """Initialize plan."""
        super().__init__(
            objective=objective or Objective(str(ObjectiveStatus.NONE_PROVIDED)),
            name=name,
            layer="plan"
        )

    @property
    def steps(self) -> List[ExecutionNode]:
        """Get plan steps."""
        return list(self.nodes.values())

    @property
    def id(self) -> str:
        """Get plan ID."""
        return self.name or "default_plan"

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

class Workflow(Plan):
    """A convenient synonym for Plan."""

    def __init__(self, objective: Optional[Objective] = None, name: Optional[str] = None):
        """Initialize workflow."""
        super().__init__(objective=objective, name=name)
