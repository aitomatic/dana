"""
Struct Function Registry for Dana

Specialized registry for struct method dispatch with composite keys.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from collections.abc import Callable
from typing import Any


class StructFunctionRegistry:
    """Registry for struct method dispatch with composite key storage.

    This registry indexes struct methods by (receiver_type, method_name) for O(1) lookup,
    enabling fast polymorphic dispatch in Dana's struct system.
    """

    def __init__(self):
        """Initialize the method registry with composite key storage."""
        # Composite key storage: (receiver_type, method_name) -> function
        self._methods: dict[tuple[str, str], Callable] = {}

        # Method metadata storage
        self._method_metadata: dict[tuple[str, str], dict[str, Any]] = {}

        # Registration order tracking
        self._registration_order: list[tuple[str, str]] = []

    def register_method_for_types(self, receiver_types: list[str], method_name: str, func: Callable) -> None:
        """Register a method for a list of receiver types.

        Args:
            receiver_types: The list of type names of the receivers
            method_name: The name of the method
            func: The callable function/method to register
        """
        for receiver_type in receiver_types:
            self.register_method(receiver_type, method_name, func)

    def register_method(self, receiver_type: str, method_name: str, func: Callable) -> None:
        """Register a method for a receiver type.

        Args:
            receiver_type: The type name of the receiver (e.g., "AgentInstance", "ResourceInstance")
            method_name: The name of the method
            func: The callable function/method to register
        """
        if not callable(func):
            raise ValueError("Method must be callable")

        key = (receiver_type, method_name)

        # Allow overwriting for now (useful during development)
        # In production, might want to warn or error
        if key in self._methods:
            # Update metadata to track overwrites
            if key in self._method_metadata:
                self._method_metadata[key]["overwrites"] = self._method_metadata[key].get("overwrites", 0) + 1

        self._methods[key] = func
        self._method_metadata[key] = {
            "registered_at": self._get_timestamp(),
            "overwrites": 0,
        }

        if key not in self._registration_order:
            self._registration_order.append(key)

    def lookup_method(self, receiver_type: str, method_name: str) -> Callable | None:
        """Fast O(1) lookup by receiver type and method name.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        return self._methods.get((receiver_type, method_name))

    def has_method(self, receiver_type: str, method_name: str) -> bool:
        """Check if a method exists for a receiver type.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            True if the method exists
        """
        return (receiver_type, method_name) in self._methods

    def lookup_method_for_instance(self, instance: Any, method_name: str) -> Callable | None:
        """Lookup method for a specific instance (extracts type automatically).

        Args:
            instance: The instance to lookup the method for
            method_name: The name of the method

        Returns:
            The registered method or None if not found
        """
        receiver_type = self._get_instance_type_name(instance)
        if receiver_type:
            return self.lookup_method(receiver_type, method_name)
        return None

    def list_methods_for_type(self, receiver_type: str) -> list[str]:
        """List all method names registered for a receiver type.

        Args:
            receiver_type: The type name of the receiver

        Returns:
            List of method names
        """
        return [method_name for (type_name, method_name) in self._registration_order if type_name == receiver_type]

    def list_receiver_types(self) -> list[str]:
        """List all receiver types that have registered methods.

        Returns:
            List of receiver type names
        """
        return list(set(type_name for (type_name, _) in self._registration_order))

    def list_all(self) -> list[tuple[str, str]]:
        """List all registered method keys.

        Returns:
            List of (receiver_type, method_name) tuples in registration order
        """
        return self._registration_order.copy()

    def get_method_metadata(self, receiver_type: str, method_name: str) -> dict[str, Any] | None:
        """Get metadata for a method.

        Args:
            receiver_type: The type name of the receiver
            method_name: The name of the method

        Returns:
            Method metadata or None if not found
        """
        return self._method_metadata.get((receiver_type, method_name))

    def find_methods_by_pattern(self, pattern: str) -> list[tuple[tuple[str, str], Callable]]:
        """Find methods by name pattern.

        Args:
            pattern: Pattern to match against method names (simple substring match)

        Returns:
            List of ((receiver_type, method_name), function) tuples
        """
        results = []
        for key, func in self._methods.items():
            if pattern.lower() in key[1].lower():  # key[1] is method_name
                results.append((key, func))
        return results

    def get_methods_by_receiver_type(self, receiver_type: str) -> dict[str, Callable]:
        """Get all methods for a specific receiver type.

        Args:
            receiver_type: The type name of the receiver

        Returns:
            Dictionary of method names to functions
        """
        methods = {}
        for (type_name, method_name), func in self._methods.items():
            if type_name == receiver_type:
                methods[method_name] = func
        return methods

    def clear(self) -> None:
        """Clear all registered methods (for testing)."""
        self._methods.clear()
        self._method_metadata.clear()
        self._registration_order.clear()

    def count(self) -> int:
        """Get the total number of registered methods."""
        return len(self._methods)

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return len(self._methods) == 0

    def _get_instance_type_name(self, instance: Any) -> str | None:
        """Get the type name from an instance.

        Handles StructType, AgentType, ResourceType, and other Dana types.

        Args:
            instance: The instance to extract type from

        Returns:
            The type name or None if unable to determine
        """
        # Try to get from struct_type attribute first (for Dana struct instances)
        if hasattr(instance, "__struct_type__"):
            struct_type = instance.__struct_type__
            if hasattr(struct_type, "name"):
                return struct_type.name

        # Try to get from agent_type attribute
        if hasattr(instance, "agent_type"):
            agent_type = instance.agent_type
            if hasattr(agent_type, "name"):
                return agent_type.name

        # Try to get from resource_type attribute
        if hasattr(instance, "resource_type"):
            resource_type = instance.resource_type
            if hasattr(resource_type, "name"):
                return resource_type.name

        # Try to get the type name from the instance class (fallback)
        if hasattr(instance, "__class__"):
            class_name = instance.__class__.__name__
            return class_name

        return None

    def _get_timestamp(self) -> float:
        """Get current timestamp for registration tracking."""
        import time

        return time.time()

    def __repr__(self) -> str:
        """String representation of the struct function registry."""
        receiver_types = self.list_receiver_types()
        return (
            f"StructFunctionRegistry("
            f"total_methods={len(self._methods)}, "
            f"receiver_types={len(receiver_types)}, "
            f"types={receiver_types[:3]}{'...' if len(receiver_types) > 3 else ''}"
            f")"
        )
