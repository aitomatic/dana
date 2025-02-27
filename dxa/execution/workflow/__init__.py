"""
FlowGraph module for workflow representation.

FlowGraphs are directed graphs that represent workflows where:
- Nodes represent tasks, decisions, or control points
- Edges represent transitions between nodes
- Validation ensures proper graph structure
"""

from .workflow_factory import WorkflowFactory, WorkflowConfig
from .workflow import Workflow
from .workflow_executor import WorkflowExecutor, WorkflowStrategy

__all__ = [
    "Workflow",
    "WorkflowFactory",
    "WorkflowStrategy",
    "WorkflowExecutor",
    "WorkflowConfig",
]
