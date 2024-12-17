"""Agent state management."""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AgentState:
    """Maintains agent state during execution."""
    
    workspace: Dict[str, Any] = field(default_factory=dict)
    history: list[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_workspace(self, data: Dict[str, Any]) -> None:
        """Update workspace with new data."""
        self.workspace.update(data)
    
    def add_to_history(self, entry: Dict[str, Any]) -> None:
        """Add entry to execution history."""
        self.history.append(entry)
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata value."""
        return self.metadata.get(key)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value 