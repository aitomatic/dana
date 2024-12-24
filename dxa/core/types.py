"""
Core types for DXA representing the fundamental concepts
of objectives, planning, and reasoning.

Objective -> Planning creates Plan[Steps] -> 
Reasoning.reason_about(Step) -> 
Signals -> Planning reassesses Objective/Plan ->
(cycle continues)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, TYPE_CHECKING
from enum import Enum
from datetime import datetime
if TYPE_CHECKING:
    from .state import AgentState, WorldState, ExecutionState

class ObjectiveStatus(Enum):
    """Status of the current objective"""
    INITIAL = "initial"
    IN_PROGRESS = "in_progress"
    NEEDS_CLARIFICATION = "needs_clarification"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Objective:
    """
    Represents what needs to be achieved. Can evolve during execution
    as new information is discovered.
    """
    original: str
    current: str  # Current understanding/interpretation
    status: ObjectiveStatus = ObjectiveStatus.INITIAL
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)

    def __init__(self, objective: str):
        """Initialize the objective"""
        if not objective:
            objective = "No objective provided"
        self.original = objective
        self.current = objective
    
    def evolve(self, new_understanding: str, reason: str) -> None:
        """Update current understanding based on new information"""
        self.history.append({
            "timestamp": datetime.now(),
            "from": self.current,
            "to": new_understanding,
            "reason": reason
        })
        self.current = new_understanding

class SignalType(Enum):
    """Type of signal"""
    DISCOVERY = "discovery"      # New information found
    STEP_COMPLETE = "step_complete"  # Step finished
    STEP_FAILED = "step_failed"      # Step failed
    OBJECTIVE_UPDATE = "objective_update"  # Objective needs updating
    RESOURCE = "resource"        # Resource-related signal

@dataclass
class Signal:
    """
    Communication between planning and reasoning layers
    about discoveries, completions, or needed changes.
    """
    type: SignalType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Context:
    """Execution context with access to all states."""
    agent_state: 'AgentState'
    world_state: 'WorldState'
    execution_state: 'ExecutionState'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "agent_state": self.agent_state,
            "world_state": self.world_state,
            "execution_state": self.execution_state
        }
