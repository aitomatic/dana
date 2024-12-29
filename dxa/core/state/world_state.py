"""
World state management.
"""

from typing import Dict, Any
from dataclasses import dataclass, field
from .base_state import BaseState

@dataclass
class WorldState(BaseState):
    """Current knowledge and context for decision making."""
    facts: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def update(self, updates: Dict[str, Any]) -> None:
        """Update world state with new knowledge."""
        self.facts.update(updates)
