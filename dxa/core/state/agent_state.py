"""Agent state management."""

from typing import List, Optional, Union
from ..types import Objective, Plan, Signal, Step
from dataclasses import dataclass, field
from .base_state import BaseState

@dataclass
class AgentState(BaseState):
    """Manages agent execution state and owns the Objective."""
    _objective: Optional[Objective] = None  # Private storage
    plan: Optional[Plan] = None
    signals: List[Signal] = field(default_factory=list)
    current_step_index: int = 0

    def set_objective(self, objective: Union[str, Objective]) -> None:
        """Set the objective, creating if needed."""
        if isinstance(objective, str):
            self._objective = Objective(original=objective, current=objective)
        else:
            self._objective = objective

    @property
    def objective(self) -> Optional[Objective]:
        """Get the current objective."""
        return self._objective

    def evolve_objective(self, new_understanding: str, reason: str) -> None:
        """Central point for objective evolution."""
        if self._objective:
            self._objective.evolve(new_understanding, reason)

    def set_plan(self, plan: Plan) -> None:
        """Set current plan."""
        self.plan = plan
        self.current_step_index = 0

    def add_signal(self, signal: Signal) -> None:
        """Add signal to state."""
        self.signals.append(signal)

    def get_signals(self) -> List[Signal]:
        """Get current signals."""
        return self.signals

    def clear_signals(self) -> None:
        """Clear all signals."""
        self.signals = []

    def advance_step(self) -> None:
        """Move to next step."""
        self.current_step_index += 1

    def get_current_step(self) -> Optional[Step]:
        """Get current step being executed."""
        if self.plan and self.current_step_index < len(self.plan.steps):
            return self.plan.steps[self.current_step_index]
        return None