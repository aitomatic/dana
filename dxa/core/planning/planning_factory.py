"""Factory for creating planners."""

from typing import List, Optional
from ..execution.execution_types import Objective
from .planner import Planner
from .base_plan import BasePlan
from .sequential_planner import SequentialPlanner
from ..workflow import Workflow

class PlanningFactory:
    """Creates and configures planners."""

    @staticmethod
    def create_sequential_planner(workflow: Optional[Workflow] = None) -> Planner:
        """Create a planner of the specified type."""
        return SequentialPlanner(workflow)

    @staticmethod
    def create_sequential_plan(objective: Objective, steps: List[str]) -> BasePlan:
        """Create a simple sequential plan from a list of step descriptions."""
        plan = BasePlan(objective)
        
        # Create nodes for each step
        prev_node = None
        for i, description in enumerate(steps):
            node = plan.add_step(
                id=f"step_{i}",
                description=description
            )
            
            # Link to previous node if exists
            if prev_node:
                plan.add_transition(prev_node.id, node.id)
            
            prev_node = node
            
        return plan
