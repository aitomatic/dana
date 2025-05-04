"""Execution-specific types for DXA."""

from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from opendxa.common.graph import Node, Edge, NodeType

class ExecutionStatus(str, Enum):
    """Status of an execution or node.
    
    This enum represents all possible states in the execution system:
    - Overall execution states (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
    - Node-specific states (IN_PROGRESS, SKIPPED, BLOCKED)
    - Control flow states (NEXT, ERROR)
    """
    # Overall execution states
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    
    # Node-specific states
    IN_PROGRESS = "IN_PROGRESS"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    
    # Control flow states
    NEXT = "NEXT"     # Move to next node
    ERROR = "ERROR"   # Handle error and redirect

class ExecutionResult(BaseModel):
    """Result of an execution node or graph."""
    node_id: str = Field(description="ID of the node that produced the result")
    status: ExecutionStatus = Field(description="Status of the execution")
    content: Dict[str, Any] = Field(default_factory=dict, description="Result content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    def __init__(self,
                 node_id: str,
                 status: ExecutionStatus,
                 content: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize execution result.
        
        Args:
            node_id: ID of the node that produced the result
            status: Status of the execution
            content: Optional result content
            metadata: Optional metadata
        """
        super().__init__(
            node_id=node_id,
            status=status,
            content=content or {},
            metadata=metadata or {}
        )

class ExecutionNodeType(str, Enum):
    """Types of execution nodes."""
    TASK = "TASK"        # For any operation that needs to be performed
    CONTROL = "CONTROL"  # For flow control (START, END)
    DATA = "DATA"        # For data operations (transform, source, sink)

class Objective(BaseModel):
    """Represents what needs to be achieved."""
    original: str = Field(description="The original objective")
    current: str = Field(description="The current objective")
    context: Dict[str, Any] = Field(default_factory=dict, description="The context of the objective")
    history: List[Dict[str, Any]] = Field(default=[], description="The history of the objective")

    def __init__(self, objective: Optional[str] = None, **data):
        """Initialize objective.
        
        Args:
            objective: The initial objective
            **data: Additional data for the objective
        """
        if objective:
            data["original"] = objective
            data["current"] = objective
        super().__init__(**data)

    def evolve(self, new_understanding: str, reason: str) -> None:
        """Evolve the objective with new understanding.
        
        Args:
            new_understanding: The new understanding of the objective
            reason: The reason for the evolution
        """
        # pylint: disable=no-member
        self.history.append({
            "previous": self.current,
            "new": new_understanding,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        self.current = new_understanding

class ExecutionNode(Node):
    """Node with execution-specific attributes."""
    objective: Optional[Objective] = None
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    step: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
    result: Optional[Dict[str, Any]] = None
    requires: Dict[str, Any] = Field(default_factory=dict)
    provides: Dict[str, Any] = Field(default_factory=dict)

    def __hash__(self) -> int:
        """Get hash of node."""
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        """Check if nodes are equal."""
        if not isinstance(other, ExecutionNode):
            return False
        return self.node_id == other.node_id

    def __init__(self,
                 node_id: str,
                 node_type: NodeType,
                 objective: Union[str, Objective],
                 status: ExecutionStatus = ExecutionStatus.PENDING,
                 step: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
                 result: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 requires: Optional[Dict[str, Any]] = None,
                 provides: Optional[Dict[str, Any]] = None,
                 **data):
        """Initialize execution node.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of the node
            objective: Objective for the node
            status: Initial status of the node
            step: Optional step function to execute
            result: Optional result of execution
            metadata: Optional metadata
            requires: Optional requirements
            provides: Optional provisions
            **data: Additional data for the node
        """
        if isinstance(objective, str):
            objective = Objective(objective)
            
        super().__init__(
            node_id=node_id,
            node_type=node_type,
            objective=objective,
            status=status,
            step=step,
            result=result,
            metadata=metadata or {},
            requires=requires or {},
            provides=provides or {},
            **data
        )

    def get_prompt(self) -> Optional[str]:
        """Get prompt from metadata if available."""
        # pylint: disable=no-member
        return self.metadata.get("prompt")

    @classmethod
    def set_prompt_in_metadata(cls, prompt: str, metadata: Dict[str, Any]) -> None:
        """Set prompt in metadata."""
        metadata["prompt"] = prompt

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "objective": self.objective.current if self.objective else None,
            "status": self.status,
            "result": self.result,
            "metadata": self.metadata,
            "requires": self.requires,
            "provides": self.provides
        }

class ExecutionEdge(Edge, BaseModel):
    """Edge with execution-specific attributes."""

    def __init__(self,
                 source: Union[str, Node],
                 target: Union[str, Node],
                 metadata: Optional[Dict[str, Any]] = None,
                 **data):
        """Initialize execution edge.
        
        Args:
            source: Source node or its ID
            target: Target node or its ID
            metadata: Optional metadata
            **data: Additional data for the edge
        """
        super().__init__(
            source=source.node_id if isinstance(source, Node) else source,
            target=target.node_id if isinstance(target, Node) else target,
            metadata=metadata or {},
            **data
        )

class ExecutionSignal(BaseModel):
    """Signal for execution navigation."""
    status: ExecutionStatus
    message: str = Field(default="", description="Optional message (e.g., error details)")
    node_id: Optional[str] = Field(default=None, description="Optional node ID")
    content: Optional[Dict[str, Any]] = Field(default=None, description="Optional content")

class ExecutionError(Exception):
    """Exception raised during execution."""
    
    def __init__(self, message: str, node_id: Optional[str] = None, signal: Optional[ExecutionSignal] = None):
        """Initialize execution error.
        
        Args:
            message: Error message
            node_id: Optional node ID
            signal: Optional execution signal
        """
        super().__init__(message)
        self.node_id = node_id
        self.signal = signal

class NodeConfig(BaseModel):
    """Configuration for a node in the execution graph."""
    node_id: str
    node_type: NodeType
    objective: str
    description: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NodeYamlConfig(BaseModel):
    """Configuration for processing a node from YAML."""
    graph: Any  # Using Any to avoid circular import
    node_data: Dict[str, Any]
    node_id: str
    config_path: Optional[str]
    custom_prompts: Optional[Dict[str, str]]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_node_config(self) -> NodeConfig:
        """Convert to node config."""
        return NodeConfig(
            node_id=self.node_id,
            node_type=self.node_data["type"],
            objective=self.node_data["objective"],
            description=self.node_data.get("description", ""),
            metadata=self.node_data.get("metadata", {})
        )
