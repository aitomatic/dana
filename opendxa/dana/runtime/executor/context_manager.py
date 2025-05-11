"""Context manager for the DANA interpreter.

This module provides utilities for managing the runtime context during execution.
"""

from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.context import RuntimeContext


class ContextManager(Loggable):
    """Manages the runtime context for the DANA interpreter.

    Responsibilities:
    - Variable resolution and scope management
    - Resource access
    - Context updates
    """

    def __init__(self, context: RuntimeContext):
        """Initialize the context manager.

        Args:
            context: The runtime context to manage
        """
        super().__init__()
        self.context = context

    def get_from_context(self, name: str, local_context: Optional[Dict[str, Any]] = None) -> Any:
        """Get a variable value from the context.

        Args:
            name: The name of the variable to get (must be in format 'scope.variable')
            local_context: Optional local context for variable resolution

        Returns:
            The variable value

        Raises:
            StateError: If the variable doesn't exist or has invalid format
        """
        # 1. Check local context first (for function parameters, etc)
        if local_context and name in local_context:
            return local_context[name]

        # 2. Validate and split the variable name
        if "." not in name:
            raise StateError(f"Variable '{name}' must include scope prefix (private.{name}, public.{name}, or system.{name})")

        scope, var_name = name.split(".", 1)
        if scope not in RuntimeScopes.ALL:
            raise StateError(f"Invalid scope '{scope}'. Must be one of: {RuntimeScopes.ALL}")

        # 3. Direct dictionary access - the core functionality
        if scope in self.context._state and var_name in self.context._state[scope]:
            return self.context._state[scope][var_name]

        # 4. Variable not found
        raise StateError(f"Variable not found: {name}")

    def set_in_context(self, name: str, value: Any) -> None:
        """Set a variable value in the context.

        Args:
            name: The name of the variable to set (must be in format 'scope.variable')
            value: The value to set

        Raises:
            StateError: If the variable scope is invalid
        """
        # Validate and split the variable name
        if "." not in name:
            raise StateError(f"Variable '{name}' must include scope prefix (local.{name}, private.{name}, public.{name}, or system.{name})")

        scope, var_name = name.split(".", 1)
        if scope not in RuntimeScopes.ALL:
            raise StateError(f"Invalid scope '{scope}'. Must be one of: {RuntimeScopes.ALL}")

        # Set the variable in the specified scope
        self.context.set(name, value)

    def get_resource(self, name: str):
        """Get a resource from the context.

        Args:
            name: The name of the resource to get

        Returns:
            The requested resource

        Raises:
            StateError: If the resource doesn't exist
        """
        return self.context.get_resource(name)

    def register_resource(self, name: str, resource: Any) -> None:
        """Register a resource in the context.

        Args:
            name: The name of the resource to register
            resource: The resource to register
        """
        self.context.register_resource(name, resource)
