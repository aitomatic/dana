"""Direct planning implementation - simplest planning pattern."""

from typing import List, Optional, Tuple
from ...types import Objective, Plan, Signal, Step

from ..base_planner import BasePlanner

class DirectPlanner(BasePlanner):
    """Simplest planning pattern - single step plan."""
    
    async def create_plan(self, objective: Objective) -> Plan:
        """Create single-step plan from objective."""
        if not hasattr(objective, 'current'):
            objective.current = objective.original

        return Plan(
            objective=objective,
            steps=[
                Step(
                    description=objective.current,
                    order=0
                )
            ]
        )

    def process_signals(
        self,
        plan: Plan,
        signals: List[Signal]
    ) -> Tuple[Optional[Plan], List[Signal]]:
        """Process signals - just pass through."""
        return None, []  # No plan updates or new signals