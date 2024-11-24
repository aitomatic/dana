"""Core types and data structures for DXA."""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

class AgentState(Enum):
    """Possible states of an agent."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"

@dataclass
class Message:
    """A message in the agent's communication."""
    content: str
    sender: str
    receiver: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Observation:
    """An observation made by the agent."""
    content: Any
    source: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionContext:
    """Context for agent execution."""
    state: AgentState
    observations: List[Observation] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    working_memory: Dict[str, Any] = field(default_factory=dict)
