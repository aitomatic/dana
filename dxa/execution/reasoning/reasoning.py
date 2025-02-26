"""Base pattern for execution reasoning."""

from abc import ABC
from typing import Optional

from ..execution_graph import ExecutionGraph
from ..execution_types import Objective, ObjectiveStatus

class Reasoning(ExecutionGraph, ABC):
    """Pattern for reasoning about execution (HOW layer)."""

    def __init__(self, objective: Optional[Objective] = None):
        super().__init__(
            objective=objective or Objective(ObjectiveStatus.NONE_PROVIDED),
            layer="reasoning"
        )
