"""Plan implementation for concrete execution steps."""

from typing import List, Optional

from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.base.execution.execution_types import Objective, ExecutionNode, ObjectiveStatus

class Plan(ExecutionGraph):
    """Concrete execution steps (WHAT layer)."""

    def __init__(self, objective: Optional[Objective] = None, name: Optional[str] = None):
        """Initialize plan."""
        super().__init__(
            objective=objective or Objective(str(ObjectiveStatus.NONE_PROVIDED)),
            name=name,
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
