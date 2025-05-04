"""Runtime state management for DANA execution."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

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

    The context provides four standard scopes:
    - private: Private to the agent, resource, or tool itself
    - group: A workgroup or shared blackboard
    - global: Openly accessible world state (time, weather, etc.)
    - execution: Execution-related mechanical state with controlled access
    """

    STANDARD_SCOPES = {"private", "group", "global", "execution"}

    def __init__(self):
        """Initializes the context with empty standard scopes and resource registry."""
        self._state: Dict[str, Dict] = {scope: {} for scope in self.STANDARD_SCOPES}
        self._resources = ResourceRegistry()

        # Initialize execution state
        self._state["execution"] = {
            "status": ExecutionStatus.IDLE,
            "current_node_id": None,
            "node_results": {},
            "history": [],
            "visited_nodes": [],
            "execution_path": [],
        }

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
        scope, path = self._validate_key(key)

        # Handle nested paths
        current = self._state[scope]
        parts = path.split(".")
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                raise StateError(f"Variable not found: {key}")
            current = current[part]
        return current

    # Execution state management
    def update_execution_node(self, node_id: str, result: Optional[Any] = None) -> None:
        """Update current execution node and record result."""
        exec_state = self._state["execution"]
        if exec_state["current_node_id"]:
            exec_state["execution_path"].append((exec_state["current_node_id"], node_id))

        exec_state["current_node_id"] = node_id
        exec_state["visited_nodes"].append(node_id)

        if result is not None:
            exec_state["node_results"][node_id] = result

    def add_execution_history(self, entry: Dict[str, Any]) -> None:
        """Add an entry to execution history."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._state["execution"]["history"].append(entry)

    def reset_execution_state(self) -> None:
        """Reset execution state to initial values."""
        self._state["execution"] = {
            "status": ExecutionStatus.IDLE,
            "current_node_id": None,
            "node_results": {},
            "history": [],
            "visited_nodes": [],
            "execution_path": [],
        }

    def get_execution_status(self) -> ExecutionStatus:
        """Get current execution status."""
        return self._state["execution"]["status"]

    def set_execution_status(self, status: ExecutionStatus) -> None:
        """Set current execution status."""
        self._state["execution"]["status"] = status

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
