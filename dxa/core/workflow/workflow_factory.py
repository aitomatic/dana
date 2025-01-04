"""Workflow factory for creating common workflow patterns."""

from typing import List, Optional, Union
from ..execution import Objective, ExecutionNode
from .workflow import Workflow
from ...common.graph import NodeType

class WorkflowFactory:
    """Factory for creating workflow patterns."""

    @classmethod
    def _add_start_end_nodes(cls, workflow: Workflow) -> None:
        """Add START and END nodes to workflow."""
        workflow.add_node(ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Begin workflow"
        ))
        workflow.add_node(ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End workflow"
        ))

    @classmethod
    def create_sequential_workflow(cls, objective: Union[str, Objective], commands: List[str]) -> Workflow:
        """Create a sequential workflow from list of commands."""
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        cls._add_start_end_nodes(workflow)

        # Create task nodes for each command
        prev_id = "START"
        for i, command in enumerate(commands):
            node_id = f"TASK_{i}"
            workflow.add_node(ExecutionNode(
                node_id=node_id,
                node_type=NodeType.TASK,
                description=command
            ))
            workflow.add_transition(prev_id, node_id)
            prev_id = node_id
            
        workflow.add_transition(prev_id, "END")
        return workflow

    @classmethod
    def create_minimal_workflow(cls, objective: Optional[Union[str, Objective]] = None) -> Workflow:
        """Create minimal workflow with START -> TASK -> END. 
        The task node will have the objective as its description.
        """
        objective = Objective(objective) if isinstance(objective, str) else objective
        workflow = Workflow(objective)
        cls._add_start_end_nodes(workflow)

        # Add task node
        workflow.add_node(ExecutionNode(
            node_id="PERFORM_TASK",
            node_type=NodeType.TASK,
            description=str(objective) if objective else ""
        ))

        workflow.add_transition("START", "PERFORM_TASK")
        workflow.add_transition("PERFORM_TASK", "END")

        return workflow
