"""Base workflow implementation using directed graphs."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, TextIO, cast, Dict, Any, Optional, List
from ..execution_graph import ExecutionGraph, ExecutionNode, ExecutionNodeType, ExecutionNodeStatus


class Workflow(ExecutionGraph):
    """Workflow class for workflow patterns.
    
    A workflow is a directed graph where:
    - Nodes represent tasks, decisions, or control points
    - Edges represent valid transitions with conditions
    - The structure defines all possible execution paths
    - State changes are tracked through transitions
    
    The workflow layer (WHY) defines high-level business processes that:
    - Capture strategic intent
    - Define success criteria
    - Specify required capabilities
    - Track overall progress
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__()
        self.name = name
        self.metadata["layer"] = "workflow"

    def add_step(self, step_id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a workflow step.
        
        Args:
            step_id: Unique identifier for the step
            description: Description of the step
            **kwargs: Additional step attributes
            
        Returns:
            The created workflow node
        """
        node = ExecutionNode(
            node_id=step_id,
            type=ExecutionNodeType.TASK,
            description=description,
            status=ExecutionNodeStatus.PENDING,
            **kwargs
        )
        self.add_node(node)
        return node

    def get_step(self, step_id: str) -> Optional[ExecutionNode]:
        """Get a workflow step by ID."""
        return self.get_node_by_id(step_id)

    def get_active_steps(self) -> List[ExecutionNode]:
        """Get all steps currently in progress."""
        return [
            node for node in self.nodes.values()
            if node.status == ExecutionNodeStatus.IN_PROGRESS
        ]

    @classmethod
    def from_yaml(cls, stream: Union[str, TextIO, Path]) -> 'Workflow':
        """Create workflow from YAML specification."""
        return cast(Workflow, ExecutionGraph._from_yaml(stream, Workflow))
