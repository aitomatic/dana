"""Factory methods for common workflow patterns."""

from typing import cast, List
from ...common.graph import GraphFactory, Node
from .workflow import Workflow

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
