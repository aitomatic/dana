"""
World state management.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import Field
from opendxa.dana.state.base_state import BaseState

class WorldState(BaseState):
    """Current knowledge and context for decision making."""
    utc_timestamp: str = Field(default="", description="The current timestamp of the world state.")
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update world state with new knowledge."""
        # pylint: disable=no-member
        self.facts.update(updates)
        self.utc_timestamp = datetime.now(timezone.utc).isoformat()