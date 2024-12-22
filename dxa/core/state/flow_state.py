"""
Flow state management. A flow is a pattern of execution, such as a research workflow,
a decision making process, an RPA workflow, some heuristics, proceess, procedure, etc.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
if TYPE_CHECKING:
    from ..flow import BaseFlow

@dataclass
class FlowState:
    """Progress through a workflow pattern."""
    flow: Optional["BaseFlow"] = field(default=None)
    current_phase: str = ""
    completed_phases: Optional[List[str]] = field(default=None)
    phase_results: Optional[Dict[str, Any]] = field(default=None)

    def __init__(self, flow: Optional["BaseFlow"] = None):
        self.flow = flow

    def update(self, phase: str, results: Dict[str, Any]) -> None:
        """Update flow state with new knowledge."""
        self.completed_phases.append(self.current_phase)
        self.current_phase = phase
        self.phase_results.update(results)
