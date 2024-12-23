"""Sequential planning implementation supporting both simple and flow-guided execution."""

from typing import List, Optional, Tuple
from ..types import Objective, Plan, Signal, Step, SignalType

from .base_planner import BasePlanner

class SequentialPlanner(BasePlanner):
    """Plans and executes steps in sequence.
    
    Handles both simple and flow-guided execution:
    - Without flow: Creates and executes single-step plan
    - With flow: Uses flow templates for multi-step execution
    
    The planner maintains step order and tracks progress regardless
    of whether it's executing a simple or complex plan.
    """
    
    async def create_plan(self, objective: Objective) -> Plan:
        """Create plan based on available flow guidance."""
        if not self.flow:
            # Simple single-step plan
            return Plan(
                objective=objective,
                steps=[Step(description=objective.current, order=0)]
            )
        
        # Use flow guidance for multi-step plan
        initial_steps = self.flow.suggest_next_steps(
            current_plan=None,
            world_state=self.get_world_state()
        )
        return Plan(objective=objective, steps=initial_steps)

    def process_signals(self, plan: Plan, signals: List[Signal]) -> Tuple[Optional[Plan], List[Signal]]:
        """Process signals and update plan if needed."""
        # Update world state from discoveries
        for signal in signals:
            if signal.type == SignalType.DISCOVERY:
                self.update_world_state(signal.content)
        
        if not self.flow:
            # Simple execution - just pass signals through
            return None, signals
            
        # Flow-guided execution - get next steps
        if any(s.type == SignalType.STEP_COMPLETE for s in signals):
            self._current_step_index += 1
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