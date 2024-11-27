"""State management for DXA agents."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class AgentState:
    """Current state of an agent."""
    name: str
    status: str  # e.g., "initializing", "ready", "running", "error", "stopped"
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
class Message:
    """A message in the agent's communication."""
    content: str
    sender: str
    receiver: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

class StateManager:
    """Manages agent state and execution context."""
    
    def __init__(self, agent_name: str):
        """Initialize state manager.
        
        Args:
            agent_name: Name of the agent this manages state for
        """
        self.agent_name = agent_name
        self.state = AgentState(
            name=agent_name,
            status="initializing"
        )
        self.observations: List[Observation] = []
        self.messages: List[Message] = []
        self.working_memory: Dict[str, Any] = {}

    def update_state(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update agent state.
        
        Args:
            status: New status string
            metadata: Optional metadata dictionary
        """
        self.state = AgentState(
            name=self.agent_name,
            status=status,
            metadata=metadata or {}
        )

    def add_observation(
        self,
        content: Any,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an observation.
        
        Args:
            content: Observation content
            source: Source of the observation
            metadata: Optional metadata
        """
        self.observations.append(
            Observation(
                content=content,
                source=source,
                metadata=metadata or {}
            )
        )

    def add_message(
        self,
        content: str,
        sender: str,
        receiver: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message.
        
        Args:
            content: Message content
            sender: Message sender
            receiver: Message receiver
            metadata: Optional metadata
        """
        self.messages.append(
            Message(
                content=content,
                sender=sender,
                receiver=receiver,
                metadata=metadata or {}
            )
        )

    def get_recent_observations(self, n: int = 5) -> List[Observation]:
        """Get n most recent observations.
        
        Args:
            n: Number of observations to return
            
        Returns:
            List of most recent observations
        """
        return self.observations[-n:]

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """Get n most recent messages.
        
        Args:
            n: Number of messages to return
            
        Returns:
            List of most recent messages
        """
        return self.messages[-n:]

    def clear_history(self) -> None:
        """Clear historical data."""
        self.observations.clear()
        self.messages.clear()
        self.working_memory.clear() 