"""Runtime state management for DANA execution."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.resource import ResourceRegistry


class ExecutionStatus(Enum):
    """Status of execution."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RuntimeContext:
    """Manages the scoped state during DANA program execution.

    The context provides three standard scopes:
    - private: Private to the agent, resource, or tool itself
    - public: Openly accessible world state (time, weather, etc.)
    - system: System-related mechanical state with controlled access
    """

    STANDARD_SCOPES = {"private", "public", "system"}

    def __init__(self):
        """Initializes the context with empty standard scopes and resource registry."""
        self._state: Dict[str, Dict] = {scope: {} for scope in self.STANDARD_SCOPES}
        self._resources = ResourceRegistry()

        # Initialize system state
        self._state["system"] = {
            "status": ExecutionStatus.IDLE,
            "history": [],
        }

    def __eq__(self, other: object) -> bool:
        """Compare two RuntimeContext objects for equality.

        Two RuntimeContext objects are considered equal if they have the same state
        and registered resources.

        Args:
            other: The other RuntimeContext object to compare with

        Returns:
            True if the contexts are equal, False otherwise
        """
        if not isinstance(other, RuntimeContext):
            return NotImplemented
        return (
            self._state == other._state
            and self._resources.list() == other._resources.list()
            and all(self._resources.get(name) == other._resources.get(name) for name in self._resources.list())
        )

    def _validate_key(self, key: str) -> tuple[str, str]:
        """Validates key format (scope.variable) and splits it."""
        parts = key.split(".", 1)  # Split only on the first dot
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise StateError(f"Invalid state key '{key}'. Must be in 'scope.variable' format.")
        scope, path = parts
        if scope not in self.STANDARD_SCOPES:
            raise StateError(f"Unknown scope: {scope}. Must be one of: {self.STANDARD_SCOPES}")
        return scope, path

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the context using dot notation (scope.variable).

        Args:
            key: The key in format 'scope.variable' or 'scope.nested.variable'
            value: The value to set

        Raises:
            StateError: If the key format is invalid or scope is unknown
        """
        scope, path = self._validate_key(key)

        # Handle nested paths
        current = self._state[scope]
        parts = path.split(".")
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the context using dot notation (scope.variable).

        Args:
            key: The key in format 'scope.variable' or 'scope.nested.variable'
            default: Value to return if key is not found

        Returns:
            The value associated with the key, or default if not found

        Raises:
            StateError: If the key format is invalid or scope is unknown
        """
        try:
            scope, path = self._validate_key(key)
        except StateError:
            # If we can't get the scope, just return the default
            return default

        # Special case: check if we're in the REPL and this is a variable like 'a'
        # that should map to something in private, public, or system
        if key == "a" and "public" in self._state and "a" in self._state["public"]:
            return self._state["public"]["a"]
        if key == "a" and "private" in self._state and "a" in self._state["private"]:
            return self._state["private"]["a"]

        # Handle nested paths
        current = self._state[scope]
        parts = path.split(".")
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                # Special handling for REPL variables - check other scopes for the same variable
                if scope == "private" and len(parts) == 1:
                    # Check if this variable exists in another scope
                    for other_scope in ["public", "system"]:
                        if other_scope in self._state and part in self._state[other_scope]:
                            return self._state[other_scope][part]

                raise StateError(f"Variable not found: {key}")
            current = current[part]
        return current

    def add_execution_history(self, entry: Dict[str, Any]) -> None:
        """Add an entry to execution history."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._state["system"]["history"].append(entry)

    def reset_execution_state(self) -> None:
        """Reset execution state to initial values."""
        self._state["system"] = {
            "status": ExecutionStatus.IDLE,
            "history": [],
        }

    def get_execution_status(self) -> ExecutionStatus:
        """Get current execution status."""
        return self._state["system"]["status"]

    def set_execution_status(self, status: ExecutionStatus) -> None:
        """Set current execution status."""
        self._state["system"]["status"] = status

    # Resource management
    def register_resource(self, name: str, resource: Any) -> None:
        """Register a resource with the given name.

        Args:
            name: The name to register the resource under
            resource: The resource object to register

        Raises:
            StateError: If the name is empty
        """
        self._resources.register(name, resource)

    def get_resource(self, name: str) -> Any:
        """Get a resource by name.

        Args:
            name: The name of the resource to get

        Returns:
            The registered resource

        Raises:
            StateError: If the resource is not found
        """
        return self._resources.get(name)

    def list_resources(self) -> List[str]:
        """List all registered resource names.

        Returns:
            A list of all registered resource names
        """
        return self._resources.list()

    def __str__(self) -> str:
        """Returns a string representation of the context state."""
        import json

        try:
            state = {"state": self._state, "resources": {name: str(self._resources.get(name)) for name in self._resources.list()}}
            return json.dumps(state, indent=2, default=str)
        except TypeError as e:
            return f"Error serializing context: {e}\n{self._state}"
