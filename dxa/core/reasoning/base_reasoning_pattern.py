"""Base pattern for execution reasoning."""

from abc import ABC
from ..execution import ExecutionGraph

class BaseReasoningPattern(ExecutionGraph, ABC):
    """Pattern for reasoning about execution (HOW layer)."""
    
    def __init__(self, objective: str):
        super().__init__(objective=objective, layer="reasoning")
