"""
Method Registry for Dana struct methods.

This module re-exports method registry functionality from the new global registry system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Re-export from the new global registry system
from dana.registry import (
    get_global_registry,
    has_struct_function,
    lookup_struct_function,
    register_struct_function,
)

# Create convenience instances for backward compatibility
global_registry = get_global_registry()
global_type_aware_method_registry = global_registry.struct_functions
global_method_registry = global_registry.struct_functions


# Create a wrapper class that provides class methods for backward compatibility
class TypeAwareMethodRegistry:
    """Type-aware method registry with class methods for backward compatibility.

    This class provides the same interface as the old TypeAwareMethodRegistry
    while delegating to the new StructFunctionRegistry.
    """

    @classmethod
    def register_method(cls, receiver_type: str, method_name: str, func) -> None:
        """Register a method for a receiver type."""
        register_struct_function(receiver_type, method_name, func)

    @classmethod
    def lookup_method(cls, receiver_type: str, method_name: str):
        """Lookup a method for a receiver type."""
        return lookup_struct_function(receiver_type, method_name)

    @classmethod
    def has_method(cls, receiver_type: str, method_name: str) -> bool:
        """Check if a method exists for a receiver type."""
        return has_struct_function(receiver_type, method_name)

    @classmethod
    def lookup_method_for_instance(cls, instance, method_name: str):
        """Lookup method for a specific instance."""
        return global_registry.struct_functions.lookup_method_for_instance(instance, method_name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered methods (for testing)."""
        global_registry.struct_functions.clear()

    def __init__(self):
        """Initialize the wrapper instance."""
        # This is needed for backward compatibility when code creates an instance
        pass

    @property
    def _storage(self):
        """Backward compatibility property for accessing the internal storage."""
        return global_registry.struct_functions._methods


class MethodRegistry:
    """Legacy method registry for backward compatibility.

    This class provides the interface expected by existing code while
    delegating to the new StructFunctionRegistry.
    """

    @classmethod
    def register_method(cls, receiver_types: list[str], method_name: str, func, source_info: str = "") -> None:
        """Register a method for multiple receiver types.

        Args:
            receiver_types: List of receiver type names
            method_name: The name of the method
            func: The callable function/method to register
            source_info: Optional source information for debugging
        """
        # Register for each receiver type
        for receiver_type in receiver_types:
            register_struct_function(receiver_type, method_name, func)

    @classmethod
    def get_method(cls, receiver_type: str, method_name: str):
        """Get a method for a specific receiver type.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        return lookup_struct_function(receiver_type, method_name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered methods (for testing)."""
        global_registry.struct_functions.clear()


# For backward compatibility - universal_method_registry referenced in other files
universal_dana_method_registry = global_type_aware_method_registry


__all__ = [
    "TypeAwareMethodRegistry",
    "MethodRegistry",
    "global_type_aware_method_registry",
    "global_method_registry",
    "universal_dana_method_registry",
    "register_struct_function",
    "lookup_struct_function",
    "has_struct_function",
]
