"""Plan implementation for concrete execution steps."""

from typing import List, Optional

from ..execution_graph import ExecutionGraph
from ..execution_types import Objective, ExecutionNode

class Plan(ExecutionGraph):
    """Concrete execution steps (WHAT layer)."""

    def __init__(self, objective: Optional[Objective] = None):
        """Initialize plan."""
        super().__init__(
            objective=objective or Objective("No objective provided"),
            layer="plan"
        )

    @property
    def steps(self) -> List[ExecutionNode]:
        """Get plan steps."""
        return list(self.nodes.values())

    @property
    def id(self) -> str:
        """Get plan ID."""
        return self.name or "default_plan"
