"""Direct planning implementation - simplest planning pattern."""

from typing import List, Optional, Tuple
from ..types import Objective, Plan, Signal, Step

from .base_planner import BasePlanner

class DirectPlanner(BasePlanner):
    """Simplest planning pattern - converts objective directly to single step."""
    
    async def create_plan(self, objective: Objective) -> Plan:
        """Create single-step plan from objective."""
        return Plan(
            objective=objective,
            steps=[Step(description=objective.current)]
        )

    async def process_signals(
        self,
        plan: Plan,
        signals: List[Signal]
    ) -> Tuple[Optional[Plan], List[Signal]]:
        """Process signals - direct planning just passes them through."""
        return None, signals 