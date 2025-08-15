"""
Method Registry for Dana struct methods.

Provides type-aware method dispatch for Dana's polymorphic system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from collections.abc import Callable
from typing import Any, Optional


class TypeAwareMethodRegistry:
    """Registry that indexes methods by (receiver_type, method_name) for O(1) lookup.

    This registry provides fast method lookup for Dana's polymorphic dispatch system.
    Methods are indexed by receiver type and method name, enabling O(1) resolution
    instead of traversing multiple lookup chains.
    """

    _instance: Optional["TypeAwareMethodRegistry"] = None
    _methods: dict[tuple[str, str], Callable] = {}

    def __new__(cls) -> "TypeAwareMethodRegistry":
        """Singleton pattern for global method registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_method(cls, receiver_type: str, method_name: str, func: Callable) -> None:
        """Register a method indexed by receiver type and method name.

        Args:
            receiver_type: The type name of the receiver (e.g., "AgentInstance", "ResourceInstance")
            method_name: The name of the method
            func: The callable function/method to register
        """
        key = (receiver_type, method_name)
        if key in cls._methods:
            # Allow overriding for now (useful during development)
            # In production, might want to warn or error
            pass
        cls._methods[key] = func

    @classmethod
    def lookup_method(cls, receiver_type: str, method_name: str) -> Callable | None:
        """Fast O(1) lookup by receiver type and method name.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        key = (receiver_type, method_name)
        return cls._methods.get(key)

    @classmethod
    def has_method(cls, receiver_type: str, method_name: str) -> bool:
        """Check if a method exists for a receiver type.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            True if the method exists
        """
        return cls.lookup_method(receiver_type, method_name) is not None

    @classmethod
    def lookup_method_for_instance(cls, instance: Any, method_name: str) -> Callable | None:
        """Lookup method for a specific instance (extracts type automatically).

        Args:
            instance: The instance to lookup the method for
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        type_name = cls._get_instance_type_name(instance)
        if type_name:
            return cls.lookup_method(type_name, method_name)
        return None

    @classmethod
    def _get_instance_type_name(cls, instance: Any) -> str | None:
        """Get the type name from an instance.

        Handles StructType, AgentType, ResourceType, and other Dana types.

        Args:
            instance: The instance to extract type from

        Returns:
            The type name or None if unable to determine
        """
        # Check for struct instances (including agents and resources)
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            if hasattr(struct_type, "name"):
                return struct_type.name

        # Check for struct instances with _type attribute
        if hasattr(instance, "_type") and hasattr(instance._type, "name"):
            return instance._type.name

        # For agent instances
        try:
            from dana.agent import AgentInstance

            if isinstance(instance, AgentInstance):
                if hasattr(instance, "agent_type") and hasattr(instance.agent_type, "name"):
                    return instance.agent_type.name
        except ImportError:
            pass

        # For resource instances
        try:
            from dana.core.resource.resource_instance import ResourceInstance

            if isinstance(instance, ResourceInstance):
                if hasattr(instance, "resource_type") and hasattr(instance.resource_type, "name"):
                    return instance.resource_type.name
        except ImportError:
            pass

        # Fallback to Python type name
        return type(instance).__name__

    @classmethod
    def clear(cls) -> None:
        """Clear all registered methods (for testing)."""
        cls._methods.clear()

    @classmethod
    def list_methods(cls, receiver_type: str | None = None) -> list[tuple[str, str]]:
        """List all registered methods, optionally filtered by receiver type.

        Args:
            receiver_type: Optional type name to filter by

        Returns:
            List of (receiver_type, method_name) tuples
        """
        if receiver_type:
            return [(rt, mn) for (rt, mn) in cls._methods.keys() if rt == receiver_type]
        return list(cls._methods.keys())


class MethodRegistry:
    """Legacy method registry for backward compatibility.

    This class provides the interface expected by existing code while
    delegating to the new TypeAwareMethodRegistry.
    """

    @classmethod
    def register_method(cls, receiver_types: list[str], method_name: str, func: Callable, source_info: str = "") -> None:
        """Register a method for multiple receiver types.

        Args:
            receiver_types: List of receiver type names
            method_name: The name of the method
            func: The callable function/method to register
            source_info: Optional source information for debugging
        """
        # Register for each receiver type
        for receiver_type in receiver_types:
            TypeAwareMethodRegistry.register_method(receiver_type, method_name, func)

    @classmethod
    def get_method(cls, receiver_type: str, method_name: str) -> Callable | None:
        """Get a method for a specific receiver type.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        return TypeAwareMethodRegistry.lookup_method(receiver_type, method_name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered methods (for testing)."""
        TypeAwareMethodRegistry.clear()


# Create global singleton instances
type_aware_method_registry = TypeAwareMethodRegistry()
method_registry = MethodRegistry()

# For backward compatibility - universal_method_registry referenced in other files
universal_dana_method_registry = type_aware_method_registry
