"""Runtime context for DANA program execution."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.exceptions import StateError


class ExecutionStatus(Enum):
    """Status of program execution."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RuntimeContext:
    """Manages the scoped state during DANA program execution."""

    def __init__(self, parent: Optional["RuntimeContext"] = None):
        """Initialize the runtime context.

        Args:
            parent: Optional parent context to inherit shared scopes from
        """
        self._parent = parent
        self._state: Dict[str, Dict[str, Any]] = {
            "local": {},  # Always fresh local scope
            "private": {},  # Inherited from parent if exists
            "public": {},  # Inherited from parent if exists
            "system": {  # Inherited from parent if exists
                "execution_status": ExecutionStatus.IDLE,
                "history": [],
            },
        }
        self._resources: Dict[str, Any] = {}

        # If parent exists, inherit shared scopes and resources
        if parent:
            for scope in RuntimeScopes.GLOBAL:
                self._state[scope] = parent._state[scope].copy()
            self._resources = parent._resources.copy()

    def _validate_key(self, key: str) -> tuple[str, str]:
        """Validates key format (scope.variable) and splits it.

        If no scope is specified, returns ('local', key). Unscoped keys must not contain a dot.
        """
        if "." not in key:
            return "local", key

        parts = key.split(".", 1)  # Split only on the first dot
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise StateError(f"Invalid state key '{key}'. Must be in 'scope.variable' format.")
        scope, path = parts
        if scope not in RuntimeScopes.ALL:
            raise StateError(f"Unknown scope: {scope}. Must be one of: {RuntimeScopes.ALL}")
        # For local scope, do not allow nested keys
        if scope == "local" and "." in path:
            raise StateError(f"Local variable names must not contain dots: '{key}'")
        return scope, path

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the context using dot notation (scope.variable).

        If no scope is specified, the value is set in the local scope.

        Args:
            key: The key in format 'scope.variable' or just 'variable'
            value: The value to set

        Raises:
            StateError: If the key format is invalid or scope is unknown
        """
        scope, var_name = self._validate_key(key)
        self._state[scope][var_name] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the context using dot notation (scope.variable).

        If no scope is specified, looks in the local scope first.

        Args:
            key: The key in format 'scope.variable' or just 'variable'
            default: Value to return if key is not found

        Returns:
            The value associated with the key, or default if not found

        Raises:
            StateError: If the key format is invalid or scope is unknown
        """
        scope, var_name = self._validate_key(key)

        if scope not in self._state or var_name not in self._state[scope]:
            if default is not None:
                return default
            raise StateError(f"Variable '{key}' not found")
        return self._state[scope][var_name]

    def get_resource(self, name: str) -> Any:
        """Get a resource from the context.

        Args:
            name: The name of the resource to get

        Returns:
            The requested resource

        Raises:
            StateError: If the resource doesn't exist
        """
        if name not in self._resources:
            raise StateError(f"Resource not found: {name}")
        return self._resources[name]

    def register_resource(self, name: str, resource: Any) -> None:
        """Register a resource in the context.

        Args:
            name: The name of the resource to register
            resource: The resource to register
        """
        self._resources[name] = resource

    def list_resources(self) -> List[str]:
        """List all registered resources.

        Returns:
            A list of resource names
        """
        return list(self._resources.keys())

    def get_execution_status(self) -> ExecutionStatus:
        """Get the current execution status.

        Returns:
            The current execution status
        """
        return self.get("system.execution_status", ExecutionStatus.IDLE)

    def set_execution_status(self, status: ExecutionStatus) -> None:
        """Set the execution status.

        Args:
            status: The new execution status
        """
        self.set("system.execution_status", status)

    def add_execution_history(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the execution history.

        Args:
            entry: The history entry to add
        """
        entry["timestamp"] = datetime.now().isoformat()
        history = self.get("system.history")
        history.append(entry)
        self.set("system.history", history)

    def reset_execution_state(self) -> None:
        """Reset the execution state to IDLE and clear history."""
        self.set_execution_status(ExecutionStatus.IDLE)
        self.set("system.history", [])

    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_context: Optional["RuntimeContext"] = None) -> "RuntimeContext":
        """Create a new RuntimeContext from a dictionary and base context, with `data` taking precedence.

        The data dictionary values will override any values already in the base context.
        Unscoped variables are placed in the local scope.

        Args:
            data: Dictionary containing context data
            base_context: Optional existing RuntimeContext

        Returns:
            A new RuntimeContext instance with the merged data
        """
        # Step 1: Create new context with base context
        context = cls(parent=base_context)

        # Step 2: Set values from data, allowing them to override base context
        for key, value in data.items():
            if "." in key:
                # Explicitly scoped variable
                scope, var_name = key.split(".", 1)
                if scope in RuntimeScopes.ALL:
                    context.set(key, value)
                else:
                    # If not a valid scope, treat as local variable
                    context.set(key, value)
            else:
                # Unscoped variable goes to local scope
                context.set(key, value)

        return context
