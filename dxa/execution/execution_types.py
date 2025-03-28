"""Execution-specific types for DXA."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime
from enum import Enum
from ..common.graph import Node, Edge, NodeType

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
        self.buffer_config = {}
    
    def get_prompt(self) -> Optional[str]:
        """Get the prompt for the node."""
        if self.metadata:
            return self.metadata['prompt']
        return None
    
    @classmethod
    def set_prompt_in_metadata(cls, prompt: str, metadata: Dict[str, Any]) -> None:
        """Set the prompt in the metadata."""
        if metadata:
            metadata['prompt'] = prompt
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation.
        
        Returns:
            Dictionary containing node data
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "description": self.description,
            "status": self.status,
            "metadata": self.metadata,
            "requires": self.requires,
            "provides": self.provides,
            "buffer_config": self.buffer_config
        }

@dataclass
class ExecutionEdge(Edge):
    """Edge with execution-specific attributes."""
    condition: Optional[str] = None
    state_updates: Dict[str, Any] = field(default_factory=dict)

class ExecutionSignalType(Enum):
    """Types of execution signals.

    Categories:
    - CONTROL_*: Execution control flow signals
    - DATA_*: Direct node-to-node data transfer
    - BUFFER_*: Buffer data transfer and management
    """
    # Control Flow - Node Status
    CONTROL_START = "node_start"        # Node begins execution
    CONTROL_COMPLETE = "node_complete"  # Node completed successfully
    CONTROL_ERROR = "node_error"        # Node execution failed
    CONTROL_SKIP = "node_skip"          # Node was skipped

    # Control Flow - Graph Status
    CONTROL_GRAPH_START = "graph_start"   # Graph execution started
    CONTROL_GRAPH_END = "graph_end"       # Graph execution completed
    CONTROL_STATE_CHANGE = "state_change"  # General execution state changes

    # Data Flow - Direct
    DATA_RESULT = "data_result"    # Node output data for next node

    # Buffer Operations
    BUFFER_DATA = "buffer_data"    # Data chunk for buffered transfer
    BUFFER_FULL = "buffer_full"    # Buffer reached capacity
    BUFFER_EMPTY = "buffer_empty"  # Buffer is empty
    BUFFER_ERROR = "buffer_error"  # Buffer operation failed

@dataclass
class ExecutionSignal:
    """Communication between execution layers."""
    type: ExecutionSignalType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

class ObjectiveStatus(Enum):
    """Status of the current objective."""
    INITIAL = "initial"
    IN_PROGRESS = "in_progress"
    NEEDS_CLARIFICATION = "needs_clarification"
    COMPLETED = "completed"
    FAILED = "failed"
    NONE_PROVIDED = "none_provided"

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
            objective = str(ObjectiveStatus.NONE_PROVIDED)
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
