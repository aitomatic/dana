"""Execution-specific types for DXA."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime
from enum import StrEnum
from ...common.graph import Node, Edge, NodeType

class ExecutionNodeStatus(StrEnum):
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
    step: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
    result: Optional[Dict[str, Any]] = None
    requires: Dict[str, Any] = field(default_factory=dict)
    provides: Dict[str, Any] = field(default_factory=dict)
    buffer_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "size": 1000,
        "mode": "streaming"
    })

    # pylint: disable=too-many-arguments
    def __init__(self, 
                 node_id: str, 
                 node_type: NodeType, 
                 description: str, 
                 status: ExecutionNodeStatus = ExecutionNodeStatus.NONE, 
                 step: Optional[Any] = None,
                 result: Optional[Dict[str, Any]] = None, 
                 metadata: Optional[Dict[str, Any]] = None,
                 requires: Optional[Dict[str, Any]] = None,
                 provides: Optional[Dict[str, Any]] = None):
        super().__init__(node_id=node_id, node_type=node_type, description=description, metadata=metadata or {})
        self.status = status
        self.step = step
        self.result = result
        self.requires = requires or {}
        self.provides = provides or {}

@dataclass 
class ExecutionEdge(Edge):
    """Edge with execution-specific attributes."""
    condition: Optional[str] = None
    state_updates: Dict[str, Any] = field(default_factory=dict)

# Signal types
class ExecutionSignalType(StrEnum):
    """Types of execution signals."""
    RESULT = "RESULT"
    ERROR = "ERROR"
    STATUS = "STATUS"
    STATE_CHANGE = "STATE_CHANGE"
    COMPLETE = "COMPLETE"
    
    # New data flow types
    DATA_CHUNK = "DATA_CHUNK"
    BUFFER_STATE = "BUFFER_STATE"
    STREAM_START = "STREAM_START"
    STREAM_END = "STREAM_END"

@dataclass
class ExecutionSignal:
    """Communication between execution layers."""
    type: ExecutionSignalType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

# Objective types
class ObjectiveStatus(StrEnum):
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

    def __init__(self, objective: Optional[str] = None):
        if not objective:
            objective = "No objective provided"
        self.original = objective
        self.current = objective
        self.status = ObjectiveStatus.INITIAL
        self.context = {}
        self.history = []
    
    def evolve(self, new_understanding: str, reason: str) -> None:
        """Evolve the objective."""
        self.history.append({
            "timestamp": datetime.now(),
            "from": self.current,
            "to": new_understanding,
            "reason": reason
        })
        self.current = new_understanding

class ExecutionError(Exception):
    """Exception for execution errors."""
    pass
