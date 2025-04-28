"""Base state management."""

from typing import Dict, Any
from pydantic import BaseModel, Field

class BaseState(BaseModel):
    """Base class for all state management."""
    
    # Add at least one field
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="The artifacts of the state")
    blackboard: Dict[str, Any] = Field(default_factory=dict, description="The shared blackboard of the state")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the blackboard using dot notation.

        Args:
            key: Dot-separated key (e.g., "a.b.c").
            default: Value to return if the key is not found.

        Returns:
            The value found at the key, or the default value.
        """
        try:
            parts = key.split('.')
            value = self.blackboard
            for part in parts:
                if not isinstance(value, dict):
                    raise KeyError(f"Intermediate path element is not a dictionary for key '{key}'")
                value = value[part]
            return value
        except KeyError:
            return default
        except TypeError:  # Handle cases where value is not subscriptable (e.g., None)
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a value on the blackboard using dot notation.

        Creates nested dictionaries as needed.

        Args:
            key: Dot-separated key (e.g., "a.b.c").
            value: The value to set.

        Raises:
            TypeError: If an intermediate path element exists but is not a dictionary.
            ValueError: If the key is empty or invalid.
        """
        if not key:
            raise ValueError("Key cannot be empty")
        parts = key.split('.')
        if any(not part for part in parts):
            raise ValueError(f"Invalid key format: '{key}'")
            
        current = self.blackboard
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                raise TypeError(f"Cannot set value for key '{key}': Element '{part}' is not a dictionary.")
            current = current[part]
        
        final_key = parts[-1]
        current[final_key] = value

    def delete(self, key: str) -> None:
        """Delete a value from the blackboard using dot notation.

        Args:
            key: Dot-separated key (e.g., "a.b.c").

        Raises:
            KeyError: If the key path is invalid or the key doesn't exist.
            ValueError: If the key is empty or invalid.
        """
        if not key:
            raise ValueError("Key cannot be empty")
        parts = key.split('.')
        if any(not part for part in parts):
            raise ValueError(f"Invalid key format: '{key}'")

        current = self.blackboard
        parent = None
        final_key = parts[-1]
        
        try:
            for _, part in enumerate(parts[:-1]):
                if not isinstance(current, dict):
                    raise KeyError(f"Intermediate path element is not a dictionary for key '{key}'")
                parent = current
                current = current[part]

            # Handle case where key has only one part
            if len(parts) == 1:
                parent = self.blackboard
            
            if isinstance(current, dict) and final_key in current:
                del current[final_key]
            elif parent and final_key in parent and len(parts) == 1:  # Special check for single part key
                del parent[final_key]
            else:
                # Reraise if the final key wasn't found where expected
                raise KeyError(f"Key '{key}' not found for deletion.")
                
        except KeyError as e:
            raise KeyError(f"Invalid path or key not found for deletion: '{key}'") from e
        except TypeError as e:  # Handle cases where value is not subscriptable (e.g., None)
            raise KeyError(f"Invalid path for deletion: '{key}'") from e

    def dump_state(self, flat: bool = False) -> Dict[str, Any]:
        """Return a copy of the blackboard state.

        Args:
            flat: If True, return a flattened dictionary with dot notation keys.
                  If False (default), return the nested dictionary structure.

        Returns:
            A dictionary representing the blackboard state.
        """
        if not flat:
            # Return a nested copy to prevent external modification
            return dict(self.blackboard)
        else:
            # Return a flattened copy
            flat_dict = {}
            
            def _flatten(current_item: Any, prefix: str = ''):
                if isinstance(current_item, dict):
                    if not current_item:  # Handle empty dictionaries
                        if prefix:
                            flat_dict[prefix] = {}
                    else:
                        for key, value in current_item.items():
                            new_key = f"{prefix}.{key}" if prefix else key
                            _flatten(value, new_key)
                else:
                    # Ensure prefix exists before assignment
                    if prefix:
                        flat_dict[prefix] = current_item
                    # Handle case where the root blackboard itself is not a dict (unlikely but safe)
                    elif not isinstance(self.blackboard, dict):
                        # Or decide on other handling, e.g., raise error or return empty
                        pass  # Or flat_dict['root'] = current_item if desired
            
            _flatten(self.blackboard)
            return flat_dict

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