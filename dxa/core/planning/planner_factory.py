"""Factory for creating planners."""

from typing import Union
from . import BasePlanner, DirectPlanner

class PlannerFactory:
    """Creates planning systems."""
    
    @classmethod
    def create_planner(cls, planner_type: Union[str, BasePlanner] = None) -> BasePlanner:
        """Create planner instance."""
        if isinstance(planner_type, BasePlanner):
            return planner_type
        planner_type = planner_type or "direct"
        if planner_type == "direct":
            return DirectPlanner()
        raise ValueError(f"Unknown planner type: {planner_type}")
