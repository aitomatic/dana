"""Provides a consistent interface for accessing different state containers using a prefix system."""

from typing import Any, Dict, Tuple, Callable, Optional
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.state.base_state import BaseState

class StateManager(Loggable):
    """Manages state access across multiple containers using a prefix system.
    
    This class provides a unified interface for accessing state across different
    containers using a simple prefix-based key system. It supports both direct
    state container access and custom state handlers for special cases.
    
    The manager supports two types of state access:
    1. Direct state container access using dot notation
    2. Custom state handlers for special processing
    
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
            state_containers: Dictionary mapping prefixes to state containers
            state_handlers: Optional dictionary mapping prefixes to handler functions.
                           Each prefix should map to a dictionary with 'get' and/or 'set'
                           keys mapping to handler functions.
        """
        super().__init__()
        if not state_containers:
            raise ValueError("StateManager requires at least one state container")
        self._state_containers = state_containers
        self._state_handlers = state_handlers or {}

    def _parse_key(self, key: str) -> Tuple[str, str]:
        """Parse a key into prefix and subkey.
        
        Args:
            key: The key to parse (e.g., 'agent.user.name')
            
        Returns:
            Tuple of (prefix, subkey)
            
        Raises:
            ValueError: If key format is invalid
        """
        parts = key.split('.', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid key format: {key}. Expected 'prefix.subkey'")
        return parts[0], parts[1]

    def _handle_state_get(self, prefix: str, subkey: str, default: Any) -> Any:
        """Handle get operations for state container keys.
        
        Args:
            prefix: The state container prefix (e.g., 'agent', 'world')
            subkey: The part of the key after the prefix
            default: Default value to return if key not found
            
        Returns:
            The retrieved value or default
        """
        target_state: BaseState = self._state_containers[prefix]
        try:
            return target_state.get(subkey, default)
        except Exception as e:
            self.logger.error(f"Error during get operation for '{prefix}.{subkey}': {e}")
            return default

    def _handle_state_set(self, prefix: str, subkey: str, value: Any) -> None:
        """Handle set operations for state container keys.
        
        Args:
            prefix: The state container prefix (e.g., 'agent', 'world')
            subkey: The part of the key after the prefix
            value: Value to set
            
        Raises:
            Exception: Re-raises underlying exceptions from state object .set() methods
        """
        target_state: BaseState = self._state_containers[prefix]
        try:
            target_state.set(subkey, value)
            self.logger.info(f"Set {prefix}.{subkey}")
        except Exception as e:
            self.logger.error(f"Error during set operation for '{prefix}.{subkey}': {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the appropriate state container or handler.
        
        The get operation follows this flow:
        1. Parse the key into prefix and subkey
        2. If prefix has a state handler, use it
        3. Otherwise, use direct state container access
        
        Args:
            key: The key to get, in the format 'prefix.subkey'
            default: Default value to return if key not found
            
        Returns:
            The retrieved value or default
        """
        try:
            prefix, subkey = self._parse_key(key)
        except ValueError as e:
            self.logger.warning(str(e))
            return default

        if prefix in self._state_handlers and 'get' in self._state_handlers[prefix]:
            return self._state_handlers[prefix]['get'](subkey, default)
        elif prefix in self._state_containers:
            return self._handle_state_get(prefix, subkey, default)
        else:
            allowed_prefixes = list(self._state_handlers.keys()) + list(self._state_containers.keys())
            self.logger.warning(f"Unknown prefix '{prefix}' in key '{key}'. Allowed: {allowed_prefixes}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a value in the appropriate state container or handler.
        
        The set operation follows this flow:
        1. Parse the key into prefix and subkey
        2. If prefix has a state handler, use it
        3. Otherwise, use direct state container access
        
        Args:
            key: The key to set, in the format 'prefix.subkey'
            value: The value to set
            
        Raises:
            ValueError: If key format is invalid
            KeyError: If prefix is unknown
        """
        try:
            prefix, subkey = self._parse_key(key)
        except ValueError as e:
            self.logger.error(str(e))
            raise

        if prefix in self._state_handlers and 'set' in self._state_handlers[prefix]:
            self._state_handlers[prefix]['set'](subkey, value)
        elif prefix in self._state_containers:
            self._handle_state_set(prefix, subkey, value)
        else:
            allowed_prefixes = list(self._state_handlers.keys()) + list(self._state_containers.keys())
            self.logger.error(f"Unknown prefix '{prefix}' in key '{key}'. Allowed: {allowed_prefixes}. Cannot set value.")
            raise KeyError(f"Invalid target prefix '{prefix}' for set operation.")

    def add_observation(self, content: str, source: str) -> None:
        """Add observation."""
        self._state_containers["observations"].append(content)
        self._state_containers["sources"].append(source)