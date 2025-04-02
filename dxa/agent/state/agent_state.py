"""Agent state management."""

from typing import List, Optional
from dataclasses import dataclass, field
from ...execution import Workflow, Objective, ExecutionSignal, ExecutionNode, Plan
from .base_state import BaseState

@dataclass
class AgentState(BaseState):
    """Manages agent execution state."""
    objective: Optional[Objective] = None
    plan: Optional[Plan] = None
    current_workflow: Optional['Workflow'] = None
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
        """Safely get current step with validation."""
        if not self.plan:
            return None
        
        step_keys = [k for k in self.plan.nodes if k.startswith("step_")]
        try:
            return self.plan.nodes[step_keys[self.current_step_index]]
        except (IndexError, KeyError):
            return None