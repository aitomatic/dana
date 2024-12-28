"""Plan implementation for concrete execution steps."""

from ..execution import ExecutionGraph, Objective

class BasePlan(ExecutionGraph):
    """Concrete execution steps (WHAT layer)."""
    
    def __init__(self, objective: Objective):
        super().__init__(objective=objective, layer="plan")
