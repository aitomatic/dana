"""Execution-specific types for DXA."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from datetime import datetime
from enum import Enum
from opendxa.common.graph import Node, Edge, NodeType

class ExecutionNodeStatus(Enum):
    """Status of execution nodes."""
    NONE = "NONE"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

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
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __init__(self, objective: Optional[str] = None):
        """Initialize objective.
        
        Args:
            objective: Initial objective text
            
        Raises:
            ValueError: If objective is empty string
        """
        if not objective:
            objective = str(ObjectiveStatus.NONE_PROVIDED)
        elif not isinstance(objective, str):
            raise ValueError("Objective must be a string")
            
        self.original = objective
        self.current = objective
        self.status = ObjectiveStatus.INITIAL
        self.context = {}
        self.history = []

    def evolve(self, new_understanding: str, reason: str) -> None:
        """Evolve the objective.
        
        Args:
            new_understanding: New understanding of the objective
            reason: Reason for the evolution
            
        Raises:
            ValueError: If new_understanding is not a string or is empty
            ValueError: If reason is not a string or is empty
        """
        if not isinstance(new_understanding, str) or not new_understanding:
            raise ValueError("New understanding must be a non-empty string")
        if not isinstance(reason, str) or not reason:
            raise ValueError("Reason must be a non-empty string")
            
        self.history.append({
            "previous": self.current,
            "new": new_understanding,
            "reason": reason,
            "timestamp": datetime.now()
        })
        self.current = new_understanding

@dataclass
class ExecutionNode(Node):
    """Node with execution-specific attributes."""
    objective: Optional[Objective] = None
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

    def __hash__(self) -> int:
        """Make node hashable by id."""
        return hash(self.node_id)
    
    def __eq__(self, other: object) -> bool:
        """Nodes are equal if they have the same id."""
        if not isinstance(other, ExecutionNode):
            return NotImplemented
        return self.node_id == other.node_id

    def __init__(self,
                 node_id: str,
                 node_type: NodeType,
                 objective: Union[str, Objective],
                 status: ExecutionNodeStatus = ExecutionNodeStatus.NONE,
                 step: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
                 result: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 requires: Optional[Dict[str, Any]] = None,
                 provides: Optional[Dict[str, Any]] = None):
        """Initialize execution node.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of the node
            objective: Objective for the node
            status: Initial status of the node
            step: Optional step function
            result: Optional result dictionary
            metadata: Optional metadata dictionary
            requires: Optional requirements dictionary
            provides: Optional provides dictionary
            
        Raises:
            ValueError: If node_id is empty
            ValueError: If objective is invalid
        """
        if not node_id:
            raise ValueError("Node ID cannot be empty")
            
        # Convert objective to string description if needed
        if isinstance(objective, str):
            description = objective
            objective_obj = Objective(objective)
        elif isinstance(objective, Objective):
            description = objective.current
            objective_obj = objective
        else:
            raise ValueError("Objective must be a string or Objective instance")
        
        # Call the base class's __init__ method
        super().__init__(node_id=node_id, node_type=node_type, description=description, metadata=metadata or {})
        
        # Set ExecutionNode-specific attributes
        self.objective = objective_obj
        self.status = status
        self.step = step
        self.result = result
        self.requires = requires or {}
        self.provides = provides or {}
        self.buffer_config = {
            "enabled": False,
            "size": 1000,
            "mode": "streaming"
        }
    
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

    def __init__(self,
                 source: Union[str, Node],
                 target: Union[str, Node],
                 condition: Optional[str] = None,
                 state_updates: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize the edge."""
        super().__init__(source, target, metadata)
        self.condition = condition
        self.state_updates = state_updates or {}

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

class ExecutionError(Exception):
    """Exception for execution errors.
    
    Attributes:
        message: Error message
        node_id: Optional ID of the node where error occurred
        signal: Optional signal that caused the error
    """
    def __init__(self, message: str, node_id: Optional[str] = None, signal: Optional[ExecutionSignal] = None):
        """Initialize execution error.
        
        Args:
            message: Error message
            node_id: Optional ID of the node where error occurred
            signal: Optional signal that caused the error
        """
        super().__init__(message)
        self.message = message
        self.node_id = node_id
        self.signal = signal
