"""Base state management."""

from typing import Dict, Any
from pydantic import BaseModel, Field

class BaseState(BaseModel):
    """Base class for all state management."""
    
    # Add at least one field
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="The artifacts of the state")
    blackboard: Dict[str, Any] = Field(default_factory=dict, description="The shared blackboard of the state")

    def reset(self) -> None:
        """Reset state to initial values. Override if needed."""
        # Reset all fields to their default values
        for field_name, field_info in type(self).model_fields.items():
            if field_info.default is not None:
                setattr(self, field_name, field_info.default)

    def update(self, updates: Dict[str, Any]) -> None:
        """Update state with new values."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value) 