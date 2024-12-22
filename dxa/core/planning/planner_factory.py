"""Factory for creating planners."""

from typing import Union
from . import BasePlanner, DirectPlanner

class PlannerFactory:
    """Creates planning systems."""
    
    @classmethod
    def create_planner(cls, planner_type: Union[str, BasePlanner] = None) -> BasePlanner:
        """Create a planner instance."""
        if isinstance(planner_type, BasePlanner):
            return planner_type
            
        # Default to DirectPlanner
        return DirectPlanner()
