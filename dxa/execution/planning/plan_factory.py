"""Factory for creating planning patterns."""

from typing import Optional, cast

from ..execution_types import Objective
from .plan import Plan
from ..execution_factory import ExecutionFactory

class PlanFactory(ExecutionFactory[Plan]):
    """Creates planning pattern instances."""
    
    # Override class variables
    graph_class = Plan
    
    @classmethod
    def create_plan(
        cls, 
        objective: Objective, 
        name: Optional[str] = None
    ) -> Plan:
        """Create a plan instance."""
        return cast(Plan, cls.create_basic_graph(objective, name))