"""Core components for DXA framework."""

__version__ = "0.1.0"

from .types import Objective, Context
from .execution_graph import ExecutionGraph

__all__ = [
    "Objective",
    "Context",
    "ExecutionGraph",
]