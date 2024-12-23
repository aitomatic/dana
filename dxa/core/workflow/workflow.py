"""Base workflow implementation using directed graphs."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dxa.common.graph import DirectedGraph, Node, Edge

@dataclass
class WorkflowNode(Node):
    """Workflow step node."""
    type: str  # START, END, TASK, DECISION, etc.
    description: str
    requires: Dict[str, Any] = field(default_factory=dict)  # Required resources/state
    provides: Dict[str, Any] = field(default_factory=dict)  # Produced outputs/state
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

@dataclass 
class WorkflowEdge(Edge):
    """Workflow transition edge."""
    condition: Optional[str] = None  # Condition for taking this path
    state_updates: Dict[str, Any] = field(default_factory=dict)  # State changes on transition
    metadata: Dict[str, Any] = field(default_factory=dict)

class Workflow(DirectedGraph):
    """Workflow class for workflow patterns.
    
    A workflow is a directed graph where:
    - Nodes represent tasks, decisions, or control points
    - Edges represent valid transitions with conditions
    - The structure defines all possible execution paths
    - State changes are tracked through transitions
    """

    def add_task(self, id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a task node to the workflow."""
        node = WorkflowNode(id, "TASK", description, **kwargs)
        self.add_node(node)
        return node

    def add_decision(self, id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a decision point to the workflow."""
        node = WorkflowNode(id, "DECISION", description, **kwargs)
        self.add_node(node)
        return node

    def add_transition(
        self,
        from_id: str,
        to_id: str,
        condition: Optional[str] = None,
        **kwargs
    ) -> WorkflowEdge:
        """Add a conditional transition between nodes."""
        edge = WorkflowEdge(from_id, to_id, condition, **kwargs)
        self.add_edge(edge)
        return edge

    def get_start(self) -> WorkflowNode:
        """Get the workflow's start node."""
        return next(
            node for node in self.nodes.values()
            if node.type == "START"
        )

    def get_ends(self) -> List[WorkflowNode]:
        """Get all possible end nodes."""
        return [
            node for node in self.nodes.values()
            if node.type == "END"
        ]