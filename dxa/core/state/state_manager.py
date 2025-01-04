"""State manager."""
from typing import Dict, Any

# TODO: do we need StateManager?
class StateManager:
    """State manager."""
    def __init__(self):
        self._state = {}
        
    def get_state(self) -> Dict[str, Any]:
        """Get state."""
        return self._state
        
    def update_state(self, key: str, value: Any) -> None:
        """Update state."""
        self._state[key] = value 

    def add_observation(self, content: str, source: str) -> None:
        """Add observation."""
        self._state["observations"].append(content)
        self._state["sources"].append(source)