"""Base state management."""

from typing import Dict, Any
from pydantic import BaseModel, Field

class BaseState(BaseModel):
    """Base class for all state management.
    
    Uses a flat registry for storing key-value data.
    Keys are strings, potentially using dot notation purely as a naming convention.
    Access is via standard dictionary methods on the 'registry' attribute.
    """
    
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="The artifacts of the state")
    registry: Dict[str, Any] = Field(default_factory=dict, description="The flat registry for shared state data")

    def reset(self) -> None:
        """Reset state to initial values. Override if needed."""
        # Reset all fields to their default values using Pydantic's mechanism if possible,
        # otherwise fallback to iterating model_fields.
        # Note: Pydantic v2 doesn't have a simple public reset method.
        initial_state = type(self)()  # Create a new instance to get defaults
        for field_name in type(self).model_fields:  # Use type(self)
            setattr(self, field_name, getattr(initial_state, field_name))

    def update(self, updates: Dict[str, Any]) -> None:
        """Update state fields with new values.
        
        Only updates top-level fields defined in the model.
        Explicitly skips updating 'registry' and 'artifacts' dict fields themselves;
        use state.registry.update() or state.artifacts.update() for modifying them.
        """
        dict_fields_to_skip = {"registry", "artifacts"}  # Fields to prevent overwriting
        
        for key, value in updates.items():
            # Check if the key is a defined model field and not one we want to skip
            if key in type(self).model_fields and key not in dict_fields_to_skip:  # Use type(self) and add skip check
                setattr(self, key, value) 