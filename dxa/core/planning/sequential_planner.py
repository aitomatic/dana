"""Sequential planning implementation."""

from typing import List, Optional, Tuple
from ..types import Objective, Plan, Signal, Step, StepStatus

from .base_planner import BasePlanner

class SequentialPlanner(BasePlanner):
    """Plans and executes steps in sequence.
    
    Handles the mechanical aspects of sequential execution:
    - Tracking current step
    - Moving to next step
    - Handling step completion/failure
    """
    
    async def create_plan(self, objective: Objective) -> Plan:
        """Create plan using flow's guidance."""
        initial_steps = self.flow.suggest_next_steps(
            current_plan=None,
            world_state=self.get_world_state()
        )
        return Plan(objective=objective, steps=initial_steps)

    def process_signals(self, plan: Plan, signals: List[Signal]) -> Tuple[Optional[Plan], List[Signal]]:
        """Update plan based on signals and flow guidance."""
        # Update world state from signals
        for signal in signals:
            if signal.type == SignalType.DISCOVERY:
                self.update_world_state(signal.content)
        
        # Check if current step is complete
        current_step = plan.steps[self._current_step_index]
        if any(s.type == SignalType.STEP_COMPLETE for s in signals):
            self._current_step_index += 1
            
        # Get next steps from flow
        next_steps = self.flow.suggest_next_steps(
            current_plan=plan,
            world_state=self.get_world_state()
        )
        
        if next_steps:
            new_plan = Plan(
                objective=plan.objective,
                steps=plan.steps[:self._current_step_index] + next_steps
            )
            if self.flow.validate_plan(new_plan):
                return new_plan, []
            
        return None, signals