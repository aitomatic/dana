"""State management for DXA agents.

This module provides classes for managing agent state, including observations,
messages, and working memory. It enables agents to maintain their execution context
and track their interaction history.

Example:
    ```python
    # Create state manager for an agent
    state = StateManager("research_agent")
    
    # Update agent state
    state.update_state("processing", {"task_id": "123"})
    
    # Record observations and messages
    state.add_observation("Found relevant data", "web_search")
    state.add_message("Please analyze this", "agent", "analyst")
    
    # Access recent history
    recent_obs = state.get_recent_observations(5)
    recent_msgs = state.get_recent_messages(3)
    ```
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class AgentState:
    """Current state of an agent.
    
    Represents a snapshot of an agent's state at a point in time.
    
    Attributes:
        name: The agent's identifier
        status: Current status (e.g., "initializing", "ready", "running", "error")
        timestamp: Unix timestamp when this state was created
        metadata: Additional state information as key-value pairs
        
    Example:
        ```python
        state = AgentState(
            name="research_agent",
            status="processing",
            metadata={"task_id": "123", "progress": 45}
        )
        ```
    """
    name: str
    status: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Observation:
    """An observation made by the agent.
    
    Represents something the agent has observed or learned during execution.
    
    Attributes:
        content: The observation content (can be any type)
        source: Source of the observation (e.g., "web_search", "user_input")
        timestamp: When the observation was made
        metadata: Additional observation context
        
    Example:
        ```python
        obs = Observation(
            content="Market growth rate: 12%",
            source="data_analysis",
            metadata={"confidence": 0.95}
        )
        ```
    """
    content: Any
    source: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    """A message in the agent's communication.
    
    Represents a communication between agents or with external entities.
    
    Attributes:
        content: Message text
        sender: Identity of message sender
        receiver: Identity of message receiver
        timestamp: When the message was sent
        metadata: Additional message context
        
    Example:
        ```python
        msg = Message(
            content="Please analyze this dataset",
            sender="coordinator",
            receiver="analyst",
            metadata={"priority": "high"}
        )
        ```
    """
    content: str
    sender: str
    receiver: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

class StateManager:
    """Manages agent state and execution context.
    
    This class provides methods for tracking an agent's state, recording
    observations and messages, and accessing execution history.
    
    Attributes:
        agent_name: Name of the agent this manages state for
        state: Current agent state
        observations: List of recorded observations
        messages: List of recorded messages
        working_memory: Dictionary for temporary data storage
        
    Example:
        ```python
        manager = StateManager("research_agent")
        
        # Update state
        manager.update_state("processing", {"task": "data_analysis"})
        
        # Record observation
        manager.add_observation(
            "Found relevant trend",
            "analysis",
            {"confidence": 0.8}
        )
        
        # Get recent history
        recent_obs = manager.get_recent_observations(5)
        ```
    """
    
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
        """Clear historical data.
        
        Clears observations, messages, and working memory while maintaining
        current state.
        """
        self.observations.clear()
        self.messages.clear()
        self.working_memory.clear() 