"""Base pattern for execution reasoning."""

from abc import ABC
from typing import Optional

from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.base.execution.execution_types import Objective

class Reasoning(ExecutionGraph, ABC):
    """Pattern for reasoning about execution (HOW layer)."""

    def __init__(self, objective: Optional[Objective] = None, name: Optional[str] = None):
        super().__init__(
            objective=objective or Objective("No objective provided"),
            name=name or "reasoning",
            layer="reasoning"
        )
