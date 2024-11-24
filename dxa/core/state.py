"""State management for DXA."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dxa.core.types import AgentState, Observation, Message, ExecutionContext

class StateManager:
    """Manages agent state and execution context."""
    
    def __init__(self):
        """Initialize state manager."""
        self.context = ExecutionContext(state=AgentState.INITIALIZING)
        self._state_history: List[Dict[str, Any]] = []

    def update_state(self, new_state: AgentState, reason: Optional[str] = None):
        """Update agent state."""
        old_state = self.context.state
        self.context.state = new_state
        
        # Record state change
        self._state_history.append({
            "timestamp": datetime.now().timestamp(),
            "old_state": old_state,
            "new_state": new_state,
            "reason": reason
        })

    def add_observation(self, content: Any, source: str, metadata: Optional[Dict] = None):
        """Add an observation."""
        observation = Observation(
            content=content,
            source=source,
            metadata=metadata or {}
        )
        self.context.observations.append(observation)

    def add_message(
        self,
        content: str,
        sender: str,
        receiver: str,
        metadata: Optional[Dict] = None
    ):
        """Add a message."""
        message = Message(
            content=content,
            sender=sender,
            receiver=receiver,
            metadata=metadata or {}
        )
        self.context.messages.append(message)

    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get state change history."""
        return self._state_history

    def get_recent_observations(self, n: int = 5) -> List[Observation]:
        """Get n most recent observations."""
        return self.context.observations[-n:]

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """Get n most recent messages."""
        return self.context.messages[-n:]

    def clear_history(self):
        """Clear historical data."""
        self._state_history.clear()
        self.context.observations.clear()
        self.context.messages.clear()
        self.context.working_memory.clear()
