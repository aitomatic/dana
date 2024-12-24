"""Plan implementation representing executable sequence of steps."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..types import Objective, StepStatus
from ..graph import DirectedGraph, Node, Edge

@dataclass
class PlanNode(Node):
    """Node representing a step in the plan."""
    description: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PlanEdge(Edge):
    """Edge representing transitions between steps."""
    condition: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class Plan(DirectedGraph):
    """
    Executable plan represented as a directed graph where:
    - Nodes are steps to be executed
    - Edges define valid transitions between steps
    - Graph structure captures execution flow
    """
    def __init__(self, objective: Objective):
        super().__init__()
        self.objective = objective
        self.history: List[Dict] = []

    def add_step(self, id: str, description: str, **kwargs) -> PlanNode:
        """Add a step to the plan."""
        node = PlanNode(id=id, description=description, **kwargs)
        self.add_node(node)
        return node

    def add_transition(
        self,
        from_id: str,
        to_id: str,
        condition: Optional[str] = None,
        **kwargs
    ) -> PlanEdge:
        """Add a transition between steps."""
        edge = PlanEdge(from_id, to_id, condition, **kwargs)
        self.add_edge(edge)
        return edge

    def update_steps(self, from_id: str, new_steps: List[PlanNode], reason: str) -> None:
        """Update plan by replacing steps from given node onwards."""
        # Record change in history
        old_nodes = list(self.nodes.values())
        self.history.append({
            "timestamp": datetime.now(),
            "from_id": from_id,
            "old_nodes": old_nodes,
            "new_steps": new_steps,
            "reason": reason
        })

        # Remove old nodes and edges
        self.remove_nodes_from(from_id)
        
        # Add new steps
        for step in new_steps:
            self.add_node(step)
            if step != new_steps[0]:  # Skip first node
                self.add_transition(new_steps[new_steps.index(step)-1].id, step.id)