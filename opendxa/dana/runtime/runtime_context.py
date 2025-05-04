"""Defines the RuntimeContext for DANA execution."""

from typing import Any, Dict, List, Optional

from opendxa.dana.exceptions import RuntimeError

# Possible dependency: Resource definitions from opendxa.agent.resource
# from opendxa.agent.resource import ResourceBase  # Example

# Possible dependency: Base state class or structure from opendxa.common
# from opendxa.common.state import HierarchicalState  # Example


class ResourceRegistry:
    """Registry for runtime resources like LLMs and tools."""

    def __init__(self):
        self._resources: Dict[str, Any] = {}

    def register(self, name: str, resource: Any) -> None:
        """Register a resource with the given name."""
        if not name:
            raise RuntimeError("Resource name cannot be empty")
        self._resources[name] = resource

    def get(self, name: str) -> Any:
        """Get a resource by name."""
        if name not in self._resources:
            raise RuntimeError(f"Resource '{name}' not found in registry")
        return self._resources[name]

    def list(self) -> List[str]:
        """List all registered resource names."""
        return list(self._resources.keys())


class StateContainer:
    """Container for state with nested key support."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self._state: Dict[str, Any] = initial_state or {}

    def _get_nested(self, keys: List[str], state: Dict[str, Any]) -> Any:
        """Helper to get nested values from state."""
        if not keys:
            return state
        key = keys[0]
        if key not in state:
            return None
        if len(keys) == 1:
            return state[key]
        return self._get_nested(keys[1:], state[key])

    def _set_nested(self, keys: List[str], value: Any, state: Dict[str, Any]) -> None:
        """Helper to set nested values in state."""
        if not keys:
            return
        key = keys[0]
        if not key:
            raise RuntimeError("State key cannot be empty")
        if len(keys) == 1:
            state[key] = value
            return
        if key not in state:
            state[key] = {}
        self._set_nested(keys[1:], value, state[key])

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from state, supporting nested keys with dot notation."""
        if not key:
            raise RuntimeError("State key cannot be empty")
        keys = key.split(".")
        result = self._get_nested(keys, self._state)
        return result if result is not None else default

    def set(self, key: str, value: Any) -> None:
        """Sets a value in state, supporting nested keys with dot notation."""
        if not key:
            raise RuntimeError("State key cannot be empty")
        keys = key.split(".")
        self._set_nested(keys, value, self._state)

    def get_all(self) -> Dict[str, Any]:
        """Returns a copy of the entire state."""
        return self._state.copy()


class RuntimeContext:
    """Holds the shared state and resources for DANA program execution."""

    def __init__(
        self,
        agent_state: Optional[StateContainer] = None,
        world_state: Optional[StateContainer] = None,
        execution_state: Optional[StateContainer] = None,
        resource_registry: Optional[ResourceRegistry] = None,
    ):
        self.agent = agent_state or StateContainer()
        self.world = world_state or StateContainer()
        self.execution = execution_state or StateContainer()
        self.resources = resource_registry or ResourceRegistry()

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the context using scoped keys (e.g., 'agent:status.ready')."""
        if not key:
            raise RuntimeError("Context key cannot be empty")
        try:
            scope, sub_key = key.split(":", 1)
        except ValueError:
            raise RuntimeError(f"Context key '{key}' must be scoped (e.g., 'scope:key').")

        if not sub_key:
            raise RuntimeError(f"Context key '{key}' must have a non-empty sub-key")

        if scope == "agent":
            return self.agent.get(sub_key, default)
        elif scope == "world":
            return self.world.get(sub_key, default)
        elif scope == "execution":
            return self.execution.get(sub_key, default)
        elif scope == "resource":
            return self.resources.get(sub_key)
        else:
            raise RuntimeError(f"Unknown context scope: '{scope}' in key '{key}'")

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the context using scoped keys."""
        if not key:
            raise RuntimeError("Context key cannot be empty")
        try:
            scope, sub_key = key.split(":", 1)
        except ValueError:
            raise RuntimeError(f"Context key '{key}' must be scoped (e.g., 'scope:key').")

        if not sub_key:
            raise RuntimeError(f"Context key '{key}' must have a non-empty sub-key")

        if scope == "agent":
            self.agent.set(sub_key, value)
        elif scope == "world":
            self.world.set(sub_key, value)
        elif scope == "execution":
            self.execution.set(sub_key, value)
        else:
            raise RuntimeError(f"Cannot set value in scope: '{scope}'. Only agent, world, execution are mutable.")

    def get_resource(self, name: str) -> Any:
        """Gets a resource object from the registry."""
        return self.resources.get(name)

    def get_full_state(self) -> Dict[str, Dict[str, Any]]:
        """Returns a snapshot of all mutable states."""
        return {
            "agent": self.agent.get_all(),
            "world": self.world.get_all(),
            "execution": self.execution.get_all(),
        }
