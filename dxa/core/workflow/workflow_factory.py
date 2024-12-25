"""Factory methods for common workflow patterns."""

from typing import List, Optional, Union
from pathlib import Path
from .workflow import Workflow, WorkflowNode

def create_workflow() -> Workflow:
    """Create a new workflow."""
    return Workflow()

def create_from_command(command: str, objective: Optional[str] = None) -> Workflow:
    """Create a workflow from a command, by calling create_from_steps."""
    return create_from_steps([command], objective)

def create_from_steps(steps: List[str], objective: Optional[str] = None) -> Workflow:
    """Create a workflow from a list of step descriptions."""
    workflow = create_workflow()
    if objective:
        workflow.objective = objective
        
    # Add START node
    workflow.add_node(WorkflowNode("start", "START", "Begin workflow"))
    
    # Add task nodes
    prev_id = "start"
    for i, step in enumerate(steps, 1):
        task_id = f"task_{i}"
        workflow.add_task(task_id, step)
        workflow.add_transition(prev_id, task_id)
        prev_id = task_id
    
    # Add END node
    workflow.add_node(WorkflowNode("end", "END", "End workflow"))
    workflow.add_transition(prev_id, "end")
    
    return workflow

def create_from_yaml(path_or_string: Union[str, Path]) -> Workflow:
    """Create workflow from YAML specification."""
    return Workflow.from_yaml(path_or_string)

def create_from_natural_language(text: str, objective: Optional[str] = None) -> Workflow:
    """Create workflow from natural language text."""
    workflow = create_workflow()
    if objective:
        workflow.objective = objective
        
    # First convert text to YAML
    yaml_data = Workflow.text_to_yaml(text)
    
    # Then create workflow from YAML
    temp_workflow = Workflow.from_yaml(yaml_data)
    
    # Copy nodes and edges to original workflow
    workflow.nodes = temp_workflow.nodes
    workflow.edges = temp_workflow.edges
    
    return workflow
