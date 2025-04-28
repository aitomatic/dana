"""Provides a consistent interface for accessing different state containers using a namespace system."""

from typing import Any, Dict, Tuple, Callable, Optional
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.state.base_state import BaseState

class StateManager(Loggable):
    """Manages state access across multiple containers using a namespace system.
    
    This class provides a unified interface for accessing state across different
    containers using a simple namespace-based key system. It supports both direct
    state container access and custom state handlers for special cases.
    
    The manager supports two types of state access:
    1. Direct state container access using dot notation (namespace.subkey)
    2. Custom state handlers for special processing based on namespace
    
    Example:
        state_manager = StateManager(
            state_containers={
                'agent': agent_state,
                'world': world_state
            },
            state_handlers={
                'special': {
                    'get': handle_special_get,
                    'set': handle_special_set
                }
            }
        )
        value = state_manager.get('agent.user.name')
        state_manager.set('world.environment.temperature', 25)
    """

    def __init__(self, 
                 state_containers: Dict[str, BaseState],
                 state_handlers: Optional[Dict[str, Dict[str, Callable]]] = None):
        """Initialize the state manager.
        
        Args:
            state_containers: Dictionary mapping namespaces to state containers.
            state_handlers: Optional dictionary mapping namespaces to handler functions.
                           Each namespace should map to a dictionary with 'get' and/or 'set'
                           keys mapping to handler functions.
        """
        super().__init__()
        if not state_containers:
            raise ValueError("StateManager requires at least one state container")
        self._state_containers = state_containers
        self._state_handlers = state_handlers or {}

    def _parse_key(self, key: str) -> Tuple[str, str]:
        """Parse a key into namespace and subkey.
        
        Args:
            key: The key to parse (e.g., 'agent.user.name')
            
        Returns:
            Tuple of (namespace, subkey)
            
        Raises:
            ValueError: If key format is invalid
        """
        parts = key.split('.', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid key format: {key}. Expected 'namespace.subkey'")
        namespace, subkey = parts[0], parts[1]
        return namespace, subkey

    def _handle_state_get(self, namespace: str, subkey: str, default: Any) -> Any:
        """Handle get operations for state container keys.
        
        Args:
            namespace: The state container namespace (e.g., 'agent', 'world')
            subkey: The part of the key after the namespace
            default: Default value to return if key not found
            
        Returns:
            The retrieved value or default
        """
        target_state: BaseState = self._state_containers[namespace]
        try:
            return target_state.get(subkey, default)
        except Exception as e:
            self.logger.error(f"Error during get operation for '{namespace}.{subkey}': {e}")
            return default

    def _handle_state_set(self, namespace: str, subkey: str, value: Any) -> None:
        """Handle set operations for state container keys.
        
        Args:
            namespace: The state container namespace (e.g., 'agent', 'world')
            subkey: The part of the key after the namespace
            value: Value to set
            
        Raises:
            Exception: Re-raises underlying exceptions from state object .set() methods
        """
        target_state: BaseState = self._state_containers[namespace]
        try:
            target_state.set(subkey, value)
            self.logger.info(f"Set {namespace}.{subkey}")
        except Exception as e:
            self.logger.error(f"Error during set operation for '{namespace}.{subkey}': {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the appropriate state container or handler.
        
        The get operation follows this flow:
        1. Parse the key into namespace and subkey
        2. If namespace has a state handler, use it
        3. Otherwise, use direct state container access
        
        Args:
            key: The key to get, in the format 'namespace.subkey'
            default: Default value to return if key not found
            
        Returns:
            The retrieved value or default
        """
        try:
            namespace, subkey = self._parse_key(key)
        except ValueError as e:
            self.logger.warning(str(e))
            return default

        if namespace in self._state_handlers and 'get' in self._state_handlers[namespace]:
            return self._state_handlers[namespace]['get'](subkey, default)
        elif namespace in self._state_containers:
            return self._handle_state_get(namespace, subkey, default)
        else:
            allowed_namespaces = list(self._state_handlers.keys()) + list(self._state_containers.keys())
            self.logger.warning(f"Unknown namespace '{namespace}' in key '{key}'. Allowed: {allowed_namespaces}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a value in the appropriate state container or handler.
        
        The set operation follows this flow:
        1. Parse the key into namespace and subkey
        2. If namespace has a state handler, use it
        3. Otherwise, use direct state container access
        
        Args:
            key: The key to set, in the format 'namespace.subkey'
            value: The value to set
            
        Raises:
            ValueError: If key format is invalid
            KeyError: If namespace is unknown
        """
        try:
            namespace, subkey = self._parse_key(key)
        except ValueError as e:
            self.logger.error(str(e))
            raise

        if namespace in self._state_handlers and 'set' in self._state_handlers[namespace]:
            self._state_handlers[namespace]['set'](subkey, value)
        elif namespace in self._state_containers:
            self._handle_state_set(namespace, subkey, value)
        else:
            allowed_namespaces = list(self._state_handlers.keys()) + list(self._state_containers.keys())
            self.logger.error(f"Unknown namespace '{namespace}' in key '{key}'. Allowed: {allowed_namespaces}. Cannot set value.")
            raise KeyError(f"Invalid target namespace '{namespace}' for set operation.")

    def add_observation(self, content: str, source: str) -> None:
        """Add observation."""
        # Assuming 'observations' and 'sources' are specific state containers/keys
        # This method doesn't seem related to the general namespace concept directly
        if "observations" in self._state_containers:
            self._state_containers["observations"].append(content)
        else:
            self.logger.warning("State container 'observations' not found for add_observation")
        if "sources" in self._state_containers:
            self._state_containers["sources"].append(source)
        else:
            self.logger.warning("State container 'sources' not found for add_observation")