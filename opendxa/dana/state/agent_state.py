"""Agent state management."""

from typing import List, Optional
from pydantic import Field
from opendxa.dana.state.base_state import BaseState

# Imports moved below just before model_rebuild()
# if TYPE_CHECKING:
#    from opendxa.base.execution.execution_types import (
#        Objective,
#        ExecutionSignal,
#    )
#    from opendxa.execution.planning.plan import Plan

class AgentState(BaseState):
    """Manages agent execution state."""
    model_config = {"arbitrary_types_allowed": True}
    
    objective: Optional['Objective'] = Field(default=None, description="The current objective of the agent")
    timezone: str = Field(default="UTC", description="The timezone of the agent")
    location: str = Field(default="", description="The location of the agent")

    def set_objective(self, objective: 'Objective') -> None:
        """Set current objective."""
        self.objective = objective

    def add_signal(self, signal: 'ExecutionSignal') -> None:
        """Add signal to state."""
        self.signals.append(signal)

    def get_signals(self) -> List['ExecutionSignal']:
        """Get current signals."""
        return self.signals

    def clear_signals(self) -> None:
        """Clear all signals."""
        self.signals = []

# Import necessary types here for model_rebuild to resolve forward references
# from opendxa.dana.execution.execution_types import (
#     Objective,
#     ExecutionSignal,
# )
# Removed Plan import: from opendxa.execution.planning.plan import Plan

# Resolve forward references now that all models should be defined/imported
# AgentState.model_rebuild()
