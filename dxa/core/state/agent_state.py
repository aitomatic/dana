"""Agent state management."""

from typing import List, Optional
from ..execution.execution_types import Objective, ExecutionSignal
from ..execution.execution_graph import ExecutionNode
from ..planning import Plan
from dataclasses import dataclass, field
from .base_state import BaseState

@dataclass
class AgentState(BaseState):
    """Manages agent execution state."""
    objective: Optional[Objective] = None
    plan: Optional[Plan] = None
    signals: List[ExecutionSignal] = field(default_factory=list)
    current_step_index: int = 0

    def set_objective(self, objective: Objective) -> None:
        """Set current objective."""
        self.objective = objective

    def set_plan(self, plan: Plan) -> None:
        """Set current plan."""
        self.plan = plan
        self.current_step_index = 0

    def add_signal(self, signal: ExecutionSignal) -> None:
        """Add signal to state."""
        self.signals.append(signal)

    def get_signals(self) -> List[ExecutionSignal]:
        """Get current signals."""
        return self.signals

    def clear_signals(self) -> None:
        """Clear all signals."""
        self.signals = []

    def advance_step(self) -> None:
        """Move to next step."""
        self.current_step_index += 1

    def get_current_step(self) -> Optional[ExecutionNode]:
        """Get current step being executed."""
        if self.plan and self.current_step_index < len(self.plan.nodes):
            return self.plan.nodes[self.current_step_index]
        return None