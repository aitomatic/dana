"""Runtime state management for DANA execution."""

import json
from opendxa.dana.exceptions import StateError

class RuntimeContext:
    """Manages the scoped state during DANA program execution."""

    # Define standard scopes if needed, although dynamically created works
    # STANDARD_SCOPES = {"agent", "world", "temp", "stmem", "ltmem", "execution"}

    def __init__(self):
        """Initializes the context with empty scopes."""
        self.scopes: dict[str, dict] = {}

    def _validate_key(self, key: str) -> tuple[str, str]:
        """Validates key format (scope.variable) and splits it."""
        parts = key.split('.', 1)  # Split only on the first dot
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise StateError(f"Invalid state key '{key}'. Must be in 'scope.variable' format.")
        # Further validation could go here (e.g., allowed chars)
        return parts[0], parts[1]

    def set(self, key: str, value: any) -> None:
        """Sets a value in the context using dot notation (scope.variable)."""
        scope_name, var_name = self._validate_key(key)

        # Create scope dict if it doesn't exist
        if scope_name not in self.scopes:
            self.scopes[scope_name] = {}

        self.scopes[scope_name][var_name] = value

    def get(self, key: str) -> any:
        """Gets a value from the context using dot notation (scope.variable)."""
        scope_name, var_name = self._validate_key(key)

        if scope_name not in self.scopes:
            raise StateError(f"Scope or path '{key}' not found: '{scope_name}' does not exist")

        scope_dict = self.scopes[scope_name]

        if var_name not in scope_dict:
            raise StateError(f"Key '{key}' not found in scope '{scope_name}'")

        return scope_dict[var_name]

    def __str__(self) -> str:
        """Returns a JSON representation of the context scopes."""
        try:
            # Use default=str for potential non-serializable types, though DANA types should be fine
            return json.dumps(self.scopes, indent=2, default=str)
        except TypeError as e:
            return f"Error serializing context: {e}\n{self.scopes}" 