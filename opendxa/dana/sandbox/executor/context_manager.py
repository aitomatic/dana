"""Context manager for the DANA interpreter.

This module provides utilities for managing the runtime context during execution.
"""

from typing import Any, Dict, Optional

from dana.sandbox.sandbox_context import SandboxContext

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.common.exceptions import StateError
from opendxa.dana.common.runtime_scopes import RuntimeScopes


class ContextManager(Loggable):
    """Manages the runtime context for the DANA interpreter.

    Responsibilities:
    - Variable resolution and scope management
    - Context updates
    """

    def __init__(self, context: SandboxContext):
        """Initialize the context manager.

        Args:
            context: The runtime context to manage
        """
        super().__init__()
        self.context = context

    def set_in_context(self, name: str, value: Any, scope: Optional[str] = None) -> None:
        """Set a variable value in the context.

        Args:
            name: The name of the variable to set (can be 'scope.name' or just 'name')
            value: The value to set
            scope: Optional scope to set the variable in. If provided, overrides any scope in name.

        Raises:
            StateError: If the variable scope is invalid
        """
        if scope is not None:
            if scope not in RuntimeScopes.ALL:
                raise StateError(f"Invalid scope '{scope}'. Must be one of: {RuntimeScopes.ALL}")
            full_name = f"{scope}.{name}"
        else:
            # If var_name is already scoped, check its scope
            if "." in name:
                candidate_scope = name.split(".", 1)[0]
                if candidate_scope not in RuntimeScopes.ALL:
                    raise StateError(f"Invalid scope '{candidate_scope}'. Must be one of: {RuntimeScopes.ALL}")
                full_name = name
            else:
                # Default to local scope
                full_name = f"local.{name}"
        self.context.set(full_name, value)

    def get_from_context(self, var_name: str, local_context: Optional[Dict[str, Any]] = None, scope: Optional[str] = None) -> Any:
        """Get a variable value from the context.

        Args:
            var_name: The name of the variable to get (can be 'scope.var' or just 'var')
            local_context: Optional local context for variable resolution
            scope: Optional scope to get the variable from. If provided, overrides any scope in var_name.

        Returns:
            The variable value

        Raises:
            StateError: If the variable doesn't exist or has invalid format
        """
        # 1. Check local context first (for function parameters, etc)
        if local_context and var_name in local_context:
            return local_context[var_name]

        # 2. Validate and split the variable name
        if scope not in RuntimeScopes.ALL:
            raise StateError(f"Invalid scope '{scope}'. Must be one of: {RuntimeScopes.ALL}")
            full_name = f"{scope}.{var_name}"
        else:
            if "." not in var_name:
                raise StateError(
                    f"Variable '{var_name}' must include scope prefix (private.{var_name}, public.{var_name}, or system.{var_name})"
                )
            candidate_scope = var_name.split(".", 1)[0]
            if candidate_scope not in RuntimeScopes.ALL:
                raise StateError(f"Invalid scope '{candidate_scope}'. Must be one of: {RuntimeScopes.ALL}")
            full_name = var_name

        # 3. Direct dictionary access - the core functionality
        scope, var_name = full_name.split(".", 1)
        if scope in self.context._state and var_name in self.context._state[scope]:
            return self.context._state[scope][var_name]

        # 4. Variable not found
        raise StateError(f"Variable not found: {full_name}")
