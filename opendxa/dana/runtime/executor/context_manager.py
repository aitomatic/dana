"""Context manager for the DANA interpreter.

This module provides utilities for managing the runtime context during execution.
"""

from typing import Any, Dict, Optional

from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.context import RuntimeContext


class ContextManager:
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
        self.context = context

    def get_variable(self, name: str, local_context: Optional[Dict[str, Any]] = None) -> Any:
        """Get a variable value from the context.

        Args:
            name: The name of the variable to get
            local_context: Optional local context for variable resolution

        Returns:
            The variable value

        Raises:
            StateError: If the variable doesn't exist
        """
        # First check if the variable is in the local context
        if local_context and name in local_context:
            value = local_context[name]
            if value is not None:
                return value

        # For dotted expressions in local context, check if the base is in context
        if local_context and "." in name:
            parts = name.split(".")
            base = parts[0]
            if base in local_context:
                # Navigate through the object attributes
                obj = local_context[base]
                for part in parts[1:]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    elif isinstance(obj, dict) and part in obj:
                        obj = obj[part]
                    else:
                        raise AttributeError(f"Object {base} has no attribute '{part}'")
                if obj is not None:
                    return obj
                raise StateError(f"Variable not found: {name}")

        # If name has no dots, try with private prefix first
        if "." not in name:
            try:
                value = self.context.get(f"private.{name}")
                if value is not None:
                    return value
            except StateError:
                pass

            # If not found in private scope or value is None, try other scopes
            for scope in ["public", "system"]:
                try:
                    value = self.context.get(f"{scope}.{name}")
                    if value is not None:
                        return value
                except StateError:
                    continue
            raise StateError(f"Variable not found: {name}")

        # If name already contains a dot, use it as is
        value = self.context.get(name)
        if value is not None:
            return value
        raise StateError(f"Variable not found: {name}")

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value in the context.

        Args:
            name: The name of the variable to set
            value: The value to set

        Raises:
            StateError: If the variable scope is invalid
        """
        # If name already contains a dot, use it as is
        if "." in name:
            self.context.set(name, value)
        else:
            # No dots, use private scope
            self.context.set(f"private.{name}", value)

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
