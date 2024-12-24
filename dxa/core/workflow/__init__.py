"""
FlowGraph module for workflow representation.

FlowGraphs are directed graphs that represent workflows where:
- Nodes represent tasks, decisions, or control points
- Edges represent transitions between nodes
- Validation ensures proper graph structure
"""

from .workflow import Workflow
from .workflow_factory import (
    create_workflow,
    create_basic_qa_workflow,
    create_research_workflow,
    create_sequential_workflow
)

__all__ = [
    "Workflow",
    "create_workflow",
    "create_basic_qa_workflow",
    "create_research_workflow",
    "create_sequential_workflow"
]
