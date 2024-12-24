"""Factory for creating planners."""

from typing import List, Optional, Union
from ..types import Objective
from .base_planner import BasePlanner
from .plan import Plan, PlanNode

class PlannerFactory:
    """Creates and configures planners."""

    @staticmethod
    def create_sequential_planner(workflow: Optional[Workflow] = None) -> BasePlanner:
        """Create a planner of the specified type."""
        return SequentialPlanner(workflow)

    @staticmethod
    def create_sequential_plan(objective: Objective, steps: List[str]) -> Plan:
        """Create a simple sequential plan from a list of step descriptions."""
        plan = Plan(objective)
        
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
