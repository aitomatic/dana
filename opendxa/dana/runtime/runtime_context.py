"""Defines the RuntimeContext for DANA execution."""

from typing import Any, Dict, Optional, List

# Possible dependency: Resource definitions from opendxa.agent.resource
# from opendxa.agent.resource import ResourceBase  # Example

# Possible dependency: Base state class or structure from opendxa.common
# from opendxa.common.state import HierarchicalState  # Example

# Placeholder for actual Resource Registry
class ResourceRegistry:
    # Reusing the simple implementation from earlier
    def __init__(self):
        self._resources: Dict[str, Any] = {}

    def register(self, name: str, resource: Any):
        # TODO: Add type checking based on ResourceBase?
        self._resources[name] = resource

    def get(self, name: str) -> Any:
        if name not in self._resources:
            # Consider using a custom DANA exception
            # from ..exceptions import ResourceNotFoundError
            # raise ResourceNotFoundError(f"Resource '{name}' not found in registry.")
            raise KeyError(f"Resource '{name}' not found in registry.")
        return self._resources[name]

    def list(self) -> List[str]:
        return list(self._resources.keys())

# Placeholder for actual State implementation (could be simple dict or more complex)
class StateContainer:
    # Reusing the simple implementation from earlier
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self._state: Dict[str, Any] = initial_state or {}

    def get(self, key: str, default: Any = None) -> Any:
        # TODO: Support nested key access? e.g., "agent:status.ready"
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        # TODO: Add validation, immutability options?
        # TODO: Support nested key setting?
        self._state[key] = value

    def get_all(self) -> Dict[str, Any]:
        return self._state.copy()


class RuntimeContext:
    """Holds the shared state (Agent, World, Execution) and resources for DANA program execution."""

    def __init__(
        self,
        agent_state: Optional[StateContainer] = None,
        world_state: Optional[StateContainer] = None,
        execution_state: Optional[StateContainer] = None,
        resource_registry: Optional[ResourceRegistry] = None,
    ):
        self.agent = agent_state or StateContainer()  # Renamed for clarity
        self.world = world_state or StateContainer()  # Renamed for clarity
        self.execution = execution_state or StateContainer()  # Renamed for clarity
        self.resources = resource_registry or ResourceRegistry()

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the context using scoped keys (e.g., 'agent:status', 'resource:my_llm')."""
        try:
            scope, sub_key = key.split(':', 1)
        except ValueError:
            # Consider using custom DANA exception
            # from ..exceptions import InvalidStateKeyError
            # raise InvalidStateKeyError(f"Context key '{key}' is not scoped.")
            raise ValueError(f"Context key '{key}' is not scoped (e.g., 'scope:key').")

        if scope == "agent":
            return self.agent.get(sub_key, default)
        elif scope == "world":
            return self.world.get(sub_key, default)
        elif scope == "execution":
            return self.execution.get(sub_key, default)
        elif scope == "resource":  # Allow fetching resource descriptions?
            # This might return the resource object itself or metadata
            return self.resources.get(sub_key)  # Let ResourceRegistry handle errors
        else:
            # from ..exceptions import InvalidStateKeyError
            # raise InvalidStateKeyError(f"Unknown context scope: '{scope}' in key '{key}'")
            raise ValueError(f"Unknown context scope: '{scope}' in key '{key}'")

    def set(self, key: str, value: Any):
        """Sets a value in the context using scoped keys. Should be mediated by interpreter/runtime."""
        # NOTE: Direct mutation by program steps might be restricted by sandbox/interpreter.
        try:
            scope, sub_key = key.split(':', 1)
        except ValueError:
            # from ..exceptions import InvalidStateKeyError
            # raise InvalidStateKeyError(f"Context key '{key}' must be scoped.")
            raise ValueError(f"Context key '{key}' must be scoped (e.g., 'scope:key').")

        if scope == "agent":
            self.agent.set(sub_key, value)
        elif scope == "world":
            self.world.set(sub_key, value)
        elif scope == "execution":
            self.execution.set(sub_key, value)
        else:
            # Resources are generally read-only during execution
            # from ..exceptions import InvalidStateKeyError
            # raise InvalidStateKeyError(f"Cannot set value in scope: {scope}")
            raise ValueError(f"Cannot set value in scope: '{scope}'. Only agent, world, execution are mutable.")

    def get_resource(self, name: str) -> Any:
        """Directly gets a resource object from the registry."""
        # This is likely used internally by interpreter/instruction handlers
        return self.resources.get(name)

    def get_full_state(self) -> Dict[str, Dict[str, Any]]:
        """Returns a snapshot of all mutable states."""
        return {
            "agent": self.agent.get_all(),
            "world": self.world.get_all(),
            "execution": self.execution.get_all(),
        } 