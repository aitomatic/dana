"""Agent state management."""

from typing import List, Optional
from pydantic import Field
from opendxa.base.execution.execution_types import Objective, ExecutionSignal
from opendxa.execution.planning.plan import Plan
from opendxa.base.state.base_state import BaseState

class AgentState(BaseState):
    """Manages agent execution state."""
    model_config = {"arbitrary_types_allowed": True}
    
    objective: Optional[Objective] = Field(default=None, description="The current objective of the agent")
    plan: Optional[Plan] = Field(default=None, description="The current plan of the agent")
    signals: List[ExecutionSignal] = Field(default=[], description="The current signals of the agent")
    timezone: str = Field(default="UTC", description="The timezone of the agent")
    location: str = Field(default="", description="The location of the agent")

    def set_objective(self, objective: Objective) -> None:
        """Set current objective."""
        self.objective = objective

    def set_plan(self, plan: Plan) -> None:
        """Set current plan."""
        self.plan = plan

    def add_signal(self, signal: ExecutionSignal) -> None:
        """Add signal to state."""
        self.signals.append(signal)

    def get_signals(self) -> List[ExecutionSignal]:
        """Get current signals."""
        return self.signals

    def clear_signals(self) -> None:
        """Clear all signals."""
        self.signals = []
