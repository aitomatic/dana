"""Agent state management."""

from typing import Dict, Any, List, Optional
from ..types import Objective, Plan, Signal, Step

class AgentState:
    """Manages agent execution state."""
    
    def __init__(self):
        self._objective: Optional[Objective] = None
        self._plan: Optional[Plan] = None
        self._signals: List[Signal] = []
        self._context: Dict[str, Any] = {}
        self._current_step_index = 0

    def set_objective(self, objective: Objective) -> None:
        """Set current objective."""
        self._objective = objective

    def set_plan(self, plan: Plan) -> None:
        """Set current plan."""
        self._plan = plan
        self._current_step_index = 0

    def add_signal(self, signal: Signal) -> None:
        """Add signal to state."""
        self._signals.append(signal)

    def get_signals(self) -> List[Signal]:
        """Get current signals."""
        return self._signals

    def clear_signals(self) -> None:
        """Clear all signals."""
        self._signals = []

    def get_context(self) -> Dict[str, Any]:
        """Get execution context."""
        return self._context

    def advance_step(self) -> None:
        """Move to next step."""
        self._current_step_index += 1

    def get_current_step(self) -> Optional[Step]:
        """Get current step being executed."""
        if self._plan and self._current_step_index < len(self._plan.steps):
            return self._plan.steps[self._current_step_index]
        return None

    @property
    def objective(self) -> Optional[Objective]:
        """Get current objective."""
        return self._objective

    @property
    def plan(self) -> Optional[Plan]:
        """Get current plan."""
        return self._plan