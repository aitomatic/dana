"""Execution-specific types for DXA."""

from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from opendxa.common.graph import Node, Edge, NodeType

class ExecutionNodeStatus(str, Enum):
    """Status of an execution node."""
    NONE = "NONE"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

class ExecutionStatus(str, Enum):
    """Status of an execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ExecutionResult(BaseModel):
    """Result of an execution node or graph."""
    node_id: str = Field(description="ID of the node that produced the result")
    status: ExecutionNodeStatus = Field(description="Status of the execution")
    content: Dict[str, Any] = Field(default_factory=dict, description="Result content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    def __init__(self,
                 node_id: str,
                 status: ExecutionNodeStatus,
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
            objective: Initial objective text
            **data: Additional data for Pydantic model
            
        Raises:
            ValueError: If objective is empty string
        """
        if not objective:
            objective = "No objective provided"
        elif not isinstance(objective, str):
            raise ValueError("Objective must be a string")
            
        super().__init__(
            original=objective,
            current=objective,
            context={},
            history=[],
            **data
        )

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
            
        # pylint: disable=no-member
        self.history.append({
            "previous": self.current,
            "new": new_understanding,
            "reason": reason,
            "timestamp": datetime.now()
        })
        self.current = new_understanding

class ExecutionNode(Node):
    """Node with execution-specific attributes."""
    objective: Optional[Objective] = None
    status: ExecutionNodeStatus = Field(default=ExecutionNodeStatus.NONE)
    step: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
    result: Optional[Dict[str, Any]] = None
    requires: Dict[str, Any] = Field(default_factory=dict)
    provides: Dict[str, Any] = Field(default_factory=dict)

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
                 provides: Optional[Dict[str, Any]] = None,
                 **data):
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
            **data: Additional data for Pydantic model
            
        Raises:
            ValueError: If node_id is empty
            ValueError: If objective is invalid
        """
        if not node_id:
            raise ValueError("Node ID cannot be empty")
            
        # Store the original description from YAML if available in data
        yaml_description = data.pop("description", None)

        # Process objective
        if isinstance(objective, str):
            objective_obj = Objective(objective)
        elif isinstance(objective, Objective):
            objective_obj = objective
        else:
            # Fallback: if objective is None or invalid, try using the yaml description
            if yaml_description:
                objective_obj = Objective(yaml_description)
            else:
                raise ValueError("Objective must be a string or Objective instance, or description must be provided in YAML")

        # Use YAML description if provided, otherwise fallback to objective's current state
        node_description = yaml_description if yaml_description is not None else objective_obj.current
        
        # Initialize Node base class
        super().__init__(
            node_id=node_id,
            node_type=node_type,
            description=node_description,  # Use the determined description
            metadata=metadata or {}
        )
        
        # Set execution-specific attributes
        self.objective = objective_obj
        self.status = status
        self.step = step
        self.result = result
        self.requires = requires or {}
        self.provides = provides or {}

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
            "objective": self.objective.current if self.objective else None,
            "status": self.status,
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
            source: Source node or node ID
            target: Target node or node ID
            metadata: Optional metadata dictionary
            **data: Additional data for Pydantic model
        """
        super().__init__(
            source=source,
            target=target,
            metadata=metadata or {},
            **data
        )

class ExecutionSignalType(Enum):
    """Types of execution signals."""
    # Control Flow
    CONTROL = "control"        # General control signal
    CONTROL_ERROR = "control_error"  # Control-specific error signal
    ERROR = "error"           # Error signal
    COMPLETE = "complete"     # Completion signal
    CONTROL_COMPLETE = "control_complete"  # Control-specific completion signal
    
    # Data Flow
    DATA = "data"            # Data signal

class ExecutionSignal(BaseModel):
    """Communication between execution layers."""
    type: ExecutionSignalType
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

class ExecutionError(Exception):
    """Base exception for execution errors."""
    def __init__(self, message: str, node_id: Optional[str] = None, signal: Optional[ExecutionSignal] = None):
        """Initialize execution error.
        
        Args:
            message: Error message
            node_id: Optional node ID where error occurred
            signal: Optional error signal
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
        """Convert YAML config to node config, injecting node-specific prompt."""
        
        # Start with metadata defined directly in the node's YAML
        node_metadata = self.node_data.get("metadata", {}).copy()
        
        # Determine the correct prompt for this node
        prompt = None
        
        # Priority 1: Custom prompts passed directly
        if self.custom_prompts and self.node_id in self.custom_prompts:
            prompt = self.custom_prompts[self.node_id]
            
        # Priority 2: Prompts defined in the graph's metadata (loaded from YAML)
        elif self.graph and "prompts" in self.graph.metadata and self.node_id in self.graph.metadata["prompts"]:
            prompt = self.graph.metadata["prompts"][self.node_id]
            
        # Priority 3: Prompt defined directly within the node's metadata in YAML (already handled by initial copy)
        # If a prompt was found from graph/custom prompts, add/overwrite it in node_metadata
        if prompt is not None:
            node_metadata["prompt"] = prompt
            
        return NodeConfig(
            node_id=self.node_id,
            node_type=self.node_data.get("type", NodeType.TASK),
            objective=self.node_data.get("objective", ""),
            description=self.node_data.get("description", ""),
            metadata=node_metadata  # Use the potentially updated metadata
        )
