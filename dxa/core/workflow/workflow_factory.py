"""Factory methods for common workflow patterns."""

import yaml
from typing import cast, List, Optional, Union
from pathlib import Path
from ...common.graph import GraphFactory, Node
from .workflow import Workflow
from ...core.resource import LLMResource
from .schema import validate_workflow_yaml

def create_workflow() -> Workflow:
    """Create a new workflow."""
    return Workflow()

def create_sequential_workflow(steps: List[Node], objective: str) -> Workflow:
    """Create a sequential workflow."""
    workflow = cast(Workflow, GraphFactory.create_sequence(steps, graph_constructor=create_workflow))
    workflow.objective = objective
    return workflow

def create_basic_qa_workflow(objective: str = "Answer the question") -> Workflow:
    """Create a basic Q&A workflow."""
    steps = [Node("ask", "TASK", "Ask a question")]
    return create_sequential_workflow(steps, objective)

def create_research_workflow(objective: str = "Research the topic") -> Workflow:
    """Create basic research workflow."""
    steps = [
        Node("gather", "TASK", "Gather information"),
        Node("analyze", "TASK", "Analyze information"),
        Node("synthesize", "TASK", "Synthesize findings")
    ]
    return create_sequential_workflow(steps, objective)

def create_from_yaml(path_or_string: Union[str, Path]) -> Workflow:
    """Create workflow from YAML specification."""
    return Workflow.from_yaml(path_or_string)

def create_from_text(text: str, objective: Optional[str] = None) -> Workflow:
    """Create workflow from natural language text."""
    workflow = create_workflow()
    if objective:
        workflow.objective = objective
        
    # First convert text to YAML
    yaml_data = text_to_yaml(text)
    
    # Then create workflow from YAML
    temp_workflow = Workflow.from_yaml(yaml_data)
    
    # Copy nodes and edges to original workflow
    workflow.nodes = temp_workflow.nodes
    workflow.edges = temp_workflow.edges
    
    return workflow

def text_to_yaml(text: str) -> str:
    """Convert natural language text to workflow YAML using LLM."""
    llm = LLMResource()
    
    prompt = f"""Convert the following natural language workflow description into YAML format.
The YAML should define nodes (tasks, decisions) and edges (transitions) in the workflow.
Include any implicit state requirements and effects.

Description:
{text}

Generate valid YAML that follows this structure:
- nodes: dictionary of workflow nodes (START, END, TASK, DECISION)
- edges: list of transitions between nodes
- metadata: optional workflow metadata

Example format:
```yaml
nodes:
  start:
    type: START
    description: "Begin workflow"
  task_1:
    type: TASK
    description: "First task"
    requires: {{input: str}}
    provides: {{output: str}}
edges:
  - from: start
    to: task_1
```
"""

    # Get YAML from LLM
    response = llm.do_query({"prompt": prompt})
    
    # Extract YAML from response
    yaml_text = response["content"].strip()
    if "```yaml" in yaml_text:
        yaml_text = yaml_text.split("```yaml")[1].split("```")[0]
    
    # Validate YAML structure
    try:
        data = yaml.safe_load(yaml_text)
        validate_workflow_yaml(data)
        return yaml_text
    except Exception as e:
        raise ValueError(f"LLM generated invalid workflow YAML: {e}") from e
