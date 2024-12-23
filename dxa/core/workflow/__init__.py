"""
FlowGraph module for workflow representation.

FlowGraphs are directed graphs that represent workflows where:
- Nodes represent tasks, decisions, or control points
- Edges represent transitions between nodes
- Validation ensures proper graph structure
"""

from .Workflow import Workflow
from .workflow_factory import create_simple_qa_workflow

__all__ = [
    "Workflow",
    "create_simple_qa_workflow"
]