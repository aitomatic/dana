"""
Function name utilities for Dana language function execution.

This module provides utilities for parsing and handling function names
in the Dana language interpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from opendxa.dana.sandbox.parser.ast import FunctionCall


class FunctionNameInfo:
    """Information about a parsed function name."""

    def __init__(self, original_name: str, func_name: str, namespace: str, full_key: str):
        """Initialize function name information.

        Args:
            original_name: The original function name from the call
            func_name: The base function name without namespace
            namespace: The namespace (e.g., 'local', 'core')
            full_key: The full key for context lookup (namespace.name)
        """
        self.original_name = original_name
        self.func_name = func_name
        self.namespace = namespace
        self.full_key = full_key

    def __str__(self) -> str:
        """String representation of function name info."""
        return f"FunctionNameInfo(original='{self.original_name}', name='{self.func_name}', namespace='{self.namespace}', key='{self.full_key}')"

    def __repr__(self) -> str:
        """Detailed representation of function name info."""
        return self.__str__()

    @property
    def is_namespaced(self) -> bool:
        """Check if this function has an explicit namespace."""
        return self.namespace != "local"

    @property
    def qualified_name(self) -> str:
        """Get the qualified name (namespace.func_name)."""
        if self.namespace == "local":
            return self.func_name
        return f"{self.namespace}.{self.func_name}"

    @classmethod
    def from_node(cls, node: FunctionCall) -> "FunctionNameInfo":
        """Parse function name information from a FunctionCall node.

        Args:
            node: The function call node

        Returns:
            Parsed function name information. For method calls (AttributeAccess), returns special
            method call info. For regular function calls, handles namespace parsing.
        """
        from opendxa.dana.sandbox.parser.ast import AttributeAccess

        # Handle AttributeAccess method calls (obj.method())
        if isinstance(node.name, AttributeAccess):
            # This is a method call - return special marker for method call handling
            original_name = str(node.name)  # String representation for debugging
            func_name = "METHOD_CALL"  # Special marker
            namespace = "method"
            full_key = "method.METHOD_CALL"

            return cls(original_name, func_name, namespace, full_key)

        # Handle regular string function names
        original_name = node.name

        # Extract base function name (removing namespace if present)
        func_name = original_name.split(".")[-1]

        # Determine namespace and full key for context lookup
        if "." in original_name:
            namespace = original_name.split(".")[0]
            func_key = original_name.split(".", 1)[1]
        else:
            namespace = "local"
            func_key = original_name

        full_key = f"{namespace}.{func_key}"

        return cls(original_name, func_name, namespace, full_key)
