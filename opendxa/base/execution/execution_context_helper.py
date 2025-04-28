"""Manages unified access to state within an ExecutionContext.

This module provides a unified interface for accessing and modifying state within
an execution context. It supports two types of state access:
1. Direct state container access using dot notation (namespace.subkey)
2. Custom state handlers for special processing based on namespace

The helper class delegates actual state management to a StateManager instance
while providing a clean, unified interface for the execution context.
"""

from typing import Any, TYPE_CHECKING, Optional, Callable, Dict
from opendxa.base.state.state_manager import StateManager
from opendxa.common.mixins.loggable import Loggable

# Use TYPE_CHECKING to avoid circular import issues
if TYPE_CHECKING:
    from opendxa.base.execution.execution_context import ExecutionContext

class ExecutionContextHelper(Loggable):
    """Helper class providing unified state access within an ExecutionContext.

    This class provides a simple interface for accessing and modifying state
    within an execution context. It supports two types of state access:

    1. Standard State Containers:
       - Direct access to state containers using dot notation
       - Managed by StateManager
       - Example: 'agent.user.name', 'world.environment.temperature'

    2. Custom State Handlers:
       - Special processing for certain state types
       - Handled by registered state handlers
       - Example: 'plan.objective', 'plan.id' (if 'plan' namespace handler is registered)

    The helper follows a consistent state access pattern:
    1. Parse key into namespace and subkey
    2. Check for state handler associated with the namespace first
    3. Fall back to StateManager for standard state access

    Usage:
        context = ExecutionContext(...)
        
        # Define state handlers for custom namespaces
        def handle_plan_get(key: str, default: Any) -> Any:
            return context.get_plan_state(key, default)
            
        def handle_plan_set(key: str, value: Any) -> None:
            context.set_plan_state(key, value)
            
        # Create helper with state containers and handlers
        helper = ExecutionContextHelper(
            context=context,
            state_containers={
                'agent': agent_state,
                'world': world_state,
                'execution': execution_state
            },
            state_handlers={
                # Handler for the 'plan' namespace
                'plan': {
                    'get': handle_plan_get,
                    'set': handle_plan_set
                }
            }
        )
        
        # Use the helper
        value = helper.get('plan.objective') # Handled by custom 'plan' handler
        helper.set('agent.user.name', 'value') # Handled by StateManager
    """

    def __init__(self, 
                 context: 'ExecutionContext',
                 state_containers: Dict[str, Any],
                 state_handlers: Optional[Dict[str, Dict[str, Callable]]] = None):
        """Initializes the helper with state containers and handlers.
        
        The initialization process:
        1. Stores reference to ExecutionContext for custom state access
        2. Initializes StateManager with the provided containers
        3. Stores state handlers for special state namespaces
        
        Args:
            context: Reference to the execution context
            state_containers: Dictionary mapping namespaces to state containers.
                            These will be managed by StateManager using dot notation.
            state_handlers: Optional dictionary mapping namespaces to handler functions.
                           Each namespace should map to a dictionary with 'get' and/or 'set'
                           keys mapping to handler functions.
                           These will be called when accessing state with their namespace.
        """
        super().__init__()
        if context is None:
            raise ValueError("ExecutionContextHelper requires a valid ExecutionContext instance.")
        
        # Store reference to ExecutionContext for custom state access
        self._context = context
        
        # Create StateManager instance to handle standard state access
        # This will manage dot notation access to the provided state containers.
        # StateManager expects namespaces. Pass handlers separately if needed,
        # or let StateManager handle its own handlers if logic changes.
        self._state_manager = StateManager(state_containers, state_handlers=None)
        
        # Store state handlers for special state types (e.g., plan namespace)
        # These will be called when accessing state with their namespace
        self._state_handlers = state_handlers or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value using a unified key string.
        
        The get operation follows this flow:
        1. Parse the key into namespace and subkey
        2. If namespace has a state handler registered here, use it
        3. Otherwise, delegate to StateManager
        
        Args:
            key: The unified key string (e.g., 'plan.id', 'agent.user.name')
            default: The value to return if the key is not found

        Returns:
            The retrieved value, or the default value if not found
        """
        # Split key into namespace and subkey (e.g., 'plan.objective' -> 'plan', 'objective')
        namespace, subkey = self._parse_key(key)
        
        # Check for state handler registered with this helper first
        if namespace in self._state_handlers and 'get' in self._state_handlers[namespace]:
            # Use state handler for this namespace (e.g., plan state)
            return self._state_handlers[namespace]['get'](subkey, default)
            
        # No specific handler here, delegate to StateManager which handles its own containers/handlers
        return self._state_manager.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value using a unified key string.
        
        The set operation follows this flow:
        1. Parse the key into namespace and subkey
        2. If namespace has a state handler registered here, use it
        3. Otherwise, delegate to StateManager
        
        Args:
            key: The unified key string (e.g., 'plan.objective', 'agent.user.name')
            value: The value to set
        
        Raises:
            ValueError: If the key format is invalid or attempts to set read-only key via handler
            KeyError: If the namespace is unknown by StateManager (when delegated)
            ReferenceError: If trying to set via a handler that requires specific context (e.g., 'plan.objective' but current_plan is None)
        """
        # Split key into namespace and subkey
        namespace, subkey = self._parse_key(key)
        
        # Check for state handler registered with this helper first
        if namespace in self._state_handlers and 'set' in self._state_handlers[namespace]:
            # Use state handler for this namespace (e.g., plan state)
            self._state_handlers[namespace]['set'](subkey, value)
        else:
            # No specific handler here, delegate to StateManager
            self._state_manager.set(key, value)

    def _parse_key(self, key: str) -> tuple[str, str]:
        """Parse a key into namespace and subkey.
        
        This method splits a dot-notation key into its namespace and subkey parts.
        For example:
            'plan.objective' -> ('plan', 'objective')
            'agent.user.name' -> ('agent', 'user.name')
        
        Args:
            key: The key to parse (e.g., 'plan.id', 'agent.user.name')
            
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