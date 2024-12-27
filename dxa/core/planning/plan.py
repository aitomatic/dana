"""Plan implementation representing executable sequence of steps."""

from typing import Dict, List, cast, Optional
from datetime import datetime
from dataclasses import dataclass, field
from ..types import Objective
from ..execution_graph import ExecutionGraph, ExecutionNode, ExecutionNodeType, ExecutionNodeStatus

@dataclass
class PlanNode(ExecutionNode):
    """Node representing a plan step."""
    estimated_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)

class Plan(ExecutionGraph):
    """
    Executable plan represented as a directed graph where:
    - Nodes are steps to be executed
    - Edges define valid transitions between steps
    - Graph structure captures execution flow
    """
    def __init__(self, objective: Objective):
        super().__init__(objective=objective)
        self.history: List[Dict] = []

    def add_step(self, step_id: str, description: str, **kwargs) -> PlanNode:
        """Add a plan step.
        
        Args:
            step_id: Unique identifier for the step
            description: Description of the step
            **kwargs: Additional step attributes
            
        Returns:
            The created plan node
        """
        node = PlanNode(
            node_id=step_id,
            type=ExecutionNodeType.TASK,
            description=description,
            status=ExecutionNodeStatus.PENDING,
            **kwargs
        )
        self.add_node(node)
        return node
    
    def update_plan(self, new_plan: 'Plan', reason: str) -> None:
        """Update current plan with changes from new plan.
        
        Args:
            new_plan: New plan to merge in
            reason: Reason for the update
        """
        # Store previous plan state
        previous_plan = cast(Plan, self.duplicate())

        self.history.append({
            'timestamp': datetime.now(),
            'reason': reason,
            'previous_plan': previous_plan,
            'new_plan': new_plan
        })
        
        # Update while preserving execution status
        self.objective = new_plan.objective
        for node_id, new_node in new_plan.nodes.items():
            if node_id in self.nodes:
                # Preserve status of existing nodes
                current_node = cast(PlanNode, self.nodes[node_id])
                new_node = cast(PlanNode, new_node)
                new_node.status = current_node.status
                new_node.actual_duration = current_node.actual_duration
            self.nodes[node_id] = new_node
            
        self.edges = new_plan.edges
        
    def to_ascii_art(self) -> str:
        """Generate ASCII art with status indicators."""
        art = super().to_ascii_art()
        status_summary = "\nStatus:\n"
        for node in self.nodes.values():
            node = cast(PlanNode, node)
            status_summary += f"  {node.node_id}: {node.status.value}\n"
        return art + status_summary
