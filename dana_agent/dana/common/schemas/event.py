from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    """
    Single observation event in the event log.
    
    NOTE: Events ONLY come from Observer. No actions, tool calls, or feedback.
    Events = Observations from environment/sensors only.
    """
    type: str = "observation"  # Always "observation" - events only from observer
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str = ""
    session_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)  # Observer data
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(uuid4()),
            "type": self.type,  # Always "observation"
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "data": self.data,  # Observer data (e.g., sensor readings)
            "metadata": self.metadata,
        }