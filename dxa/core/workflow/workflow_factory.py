"""Factory methods for common workflow patterns."""

from typing import List, Optional, Union, cast
from pathlib import Path
from ..execution import ExecutionGraph, ExecutionNode, Objective
from .workflow import Workflow
from ...common.graph import NodeType

class WorkflowFactory:
    """Factory for creating workflows."""

    @classmethod
    def create_basic(cls) -> Workflow:
        """Create a new workflow."""
        return Workflow()

    @classmethod
    def create_from_command(cls, command: str, objective: Optional[str] = None) -> Workflow:
        """Create a workflow from a command, by calling create_from_steps."""
        return cls.create_from_steps([command], objective)

    @classmethod
    def create_from_steps(cls, steps: List[str], objective: Optional[str] = None) -> Workflow:
        """Create a workflow from a list of step descriptions."""
        workflow = cls.create_basic()
        if objective is not None:
            workflow.objective = Objective(objective)
            
        # Add START node
        workflow.add_node(ExecutionNode(
            node_id="start",
            node_type=NodeType.START,
            description="Begin workflow"
        ))
        
        # Add task nodes
        prev_id = "start"
        for i, step in enumerate(steps, 1):
            task_id = f"task_{i}"
            workflow.add_node(ExecutionNode(
                node_id=task_id,
                node_type=NodeType.TASK,
                description=step
            ))
            workflow.add_transition(prev_id, task_id)
            prev_id = task_id
        
        # Add END node
        workflow.add_node(ExecutionNode(
            node_id="end",
            node_type=NodeType.END,
            description="End workflow"
        ))
        workflow.add_transition(prev_id, "end")
        
        return workflow

    @classmethod
    def create_from_yaml(cls, path_or_string: Union[str, Path]) -> Workflow:
        """Create workflow from YAML specification."""
        return cast(Workflow, ExecutionGraph.from_yaml(path_or_string))

    @classmethod
    def create_from_natural_language(cls, text: str, objective: Optional[str] = None) -> Workflow:
        """Create workflow from natural language text."""
        workflow = WorkflowFactory.create_basic()
        if objective is not None:
            workflow.objective = Objective(objective)
            
        # First convert natural language to YAML
        yaml_data = Workflow.natural_language_to_yaml(text)
        
        # Then create workflow from YAML
        temp_workflow = cast(Workflow, ExecutionGraph.from_yaml(yaml_data))
        
        # Copy nodes and edges to original workflow
        workflow.nodes = temp_workflow.nodes
        workflow.edges = temp_workflow.edges
        
        return workflow

    @classmethod
    def create_from_objective(cls, objective: Union[str, Objective]) -> Workflow:
        """Create a simple workflow for question answering."""
        workflow = WorkflowFactory.create_basic()
        
        # Add START node
        workflow.add_node(ExecutionNode(
            node_id="start",
            node_type=NodeType.START,
            description="Begin workflow"
        ))
        
        # Add question task
        workflow.add_node(ExecutionNode(
            node_id="answer_question",
            node_type=NodeType.TASK,
            description=objective if isinstance(objective, str) else objective.original
        ))
        workflow.add_transition("start", "answer_question")
        
        # Add END node
        workflow.add_node(ExecutionNode(
            node_id="end",
            node_type=NodeType.END,
            description="End workflow"
        ))
        workflow.add_transition("answer_question", "end")
        
        return workflow
