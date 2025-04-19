"""Factory for creating planning patterns."""

from typing import Optional, cast

from opendxa.base.execution.execution_types import Objective
from opendxa.execution.planning.plan import Plan
from opendxa.base.execution.execution_factory import ExecutionFactory

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