"""
Flow state management. A flow is a pattern of execution, such as a research workflow,
a decision making process, an RPA workflow, some heuristics, proceess, procedure, etc.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from .base_state import BaseState
if TYPE_CHECKING:
    from ..workflow import BaseFlow

@dataclass
class FlowState(BaseState):
    """Progress through a workflow pattern."""
    flow: Optional["BaseFlow"] = None
    current_phase: str = ""
    completed_phases: List[str] = field(default_factory=list)
    phase_results: Dict[str, Any] = field(default_factory=dict)

    def set_flow(self, flow: "BaseFlow") -> None:
        """Set current flow."""
        self.flow = flow

    def update(self, phase: str, results: Dict[str, Any]) -> None:
        """Update flow state with new knowledge."""
        self.completed_phases.append(self.current_phase)
        self.current_phase = phase
        self.phase_results.update(results)
