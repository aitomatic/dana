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
    create_from_command,
    create_from_steps,
    create_from_yaml,
    create_from_natural_language,
)

__all__ = [
    "Workflow",
    "create_workflow",
    "create_from_command",
    "create_from_steps",
    "create_from_yaml",
    "create_from_natural_language",
]
