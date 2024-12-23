"""Base state management."""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class BaseState:
    """Base class for all state management."""
    
    def initialize(self) -> None:
        """Initialize state. Override if needed."""
        pass

    def reset(self) -> None:
        """Reset state to initial values. Override if needed."""
        # Reset all fields to their default values
        for field_name, field_def in self.__dataclass_fields__.items():
            if hasattr(field_def, "default_factory"):
                setattr(self, field_name, field_def.default_factory())
            else:
                setattr(self, field_name, field_def.default)

    def update(self, updates: Dict[str, Any]) -> None:
        """Update state with new values."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value) 