"""Execution-specific types for DXA."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum
from datetime import datetime
from ...common.graph.node import Node
from ...common.graph.edge import Edge

if TYPE_CHECKING:
    from ..state import AgentState, WorldState, ExecutionState
    from ..workflow import Workflow
    from ..planning import BasePlan

# Node types
class ExecutionNodeType(Enum):
    """Execution-specific node types."""
    REGULAR = "REGULAR"
    START = "START"
    END = "END"
    TASK = "TASK"
    CONDITION = "CONDITION"
    FORK = "FORK"
    JOIN = "JOIN"
    LOOP = "LOOP"
    SUBGRAPH = "SUBGRAPH"

class ExecutionNodeStatus(Enum):
    """Status of execution nodes."""
    NONE = "NONE"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

@dataclass
class ExecutionNode(Node):
    """Node with execution-specific attributes."""
    status: ExecutionNodeStatus = ExecutionNodeStatus.NONE
    result: Optional[Dict[str, Any]] = None
    requires: Dict[str, Any] = field(default_factory=dict)
    provides: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, 
                 node_id: str, 
                 node_type: ExecutionNodeType, 
                 description: str, 
                 status: ExecutionNodeStatus = ExecutionNodeStatus.NONE, 
                 result: Optional[Dict[str, Any]] = None, 
                 metadata: Optional[Dict[str, Any]] = None,
                 requires: Optional[Dict[str, Any]] = None,
                 provides: Optional[Dict[str, Any]] = None):
        super().__init__(node_id=node_id, type=node_type.value, description=description, metadata=metadata or {})
        self.status = status
        self.result = result
        self.requires = requires or {}
        self.provides = provides or {}

@dataclass 
class ExecutionEdge(Edge):
    """Edge with execution-specific attributes."""
    condition: Optional[str] = None
    state_updates: Dict[str, Any] = field(default_factory=dict)

# Signal types
class ExecutionSignalType(Enum):
    """Signal types for execution layers."""
    # Common signals
    STATE_CHANGE = "STATE_CHANGE"
    STEP_COMPLETE = "STEP_COMPLETE"
    STEP_FAILED = "STEP_FAILED"
    INTERRUPT = "INTERRUPT"

    # Workflow layer (WHY)
    OBJECTIVE_UPDATE = "OBJECTIVE_UPDATE"
    NEED_CLARIFICATION = "NEED_CLARIFICATION"

    # Planning layer (WHAT)
    DISCOVERY = "DISCOVERY"
    DEPENDENCY_BLOCKED = "DEPENDENCY_BLOCKED"

    # Reasoning layer (HOW)
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    RESOURCE = "RESOURCE"

@dataclass
class ExecutionSignal:
    """Communication between execution layers."""
    type: ExecutionSignalType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

# Objective types
class ObjectiveStatus(Enum):
    """Status of the current objective."""
    INITIAL = "initial"
    IN_PROGRESS = "in_progress"
    NEEDS_CLARIFICATION = "needs_clarification"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Objective:
    """Represents what needs to be achieved."""
    original: str
    current: str
    status: ObjectiveStatus = ObjectiveStatus.INITIAL
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)

    def __init__(self, objective: str):
        if not objective:
            objective = "No objective provided"
        self.original = objective
        self.current = objective
    
    def evolve(self, new_understanding: str, reason: str) -> None:
        """Evolve the objective."""
        self.history.append({
            "timestamp": datetime.now(),
            "from": self.current,
            "to": new_understanding,
            "reason": reason
        })
        self.current = new_understanding

# Context types
@dataclass
class ExecutionContext:
    """Execution context with access to all states."""
    agent_state: 'AgentState'
    world_state: 'WorldState'
    execution_state: 'ExecutionState'
    current_workflow: 'Workflow'
    current_plan: 'BasePlan'

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "agent_state": self.agent_state,
            "world_state": self.world_state,
            "execution_state": self.execution_state,
            "current_workflow": self.current_workflow,
            "current_plan": self.current_plan
        }

class ExecutionError(Exception):
    """Exception for execution errors."""
    pass
