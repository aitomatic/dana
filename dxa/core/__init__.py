"""Core components for DXA framework."""

__version__ = "0.1.0"

from .execution.execution_types import Objective, ExecutionContext
from .execution.execution_graph import ExecutionGraph

__all__ = [
    "Objective",
    "ExecutionContext",
    "ExecutionGraph",
]