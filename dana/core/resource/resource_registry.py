"""
Resource Type Registry

Efficient registry for resource types, separate from struct types for performance.
"""

from typing import Any, Optional

from .resource_instance import ResourceInstance
from .resource_type import ResourceType


class ResourceTypeRegistry:
    """Efficient registry for resource types only (no instance tracking)."""

    _instance: Optional["ResourceTypeRegistry"] = None
    _resource_types: dict[str, ResourceType] = {}

    def __new__(cls) -> "ResourceTypeRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_resource(cls, resource_type: ResourceType) -> None:
        """Register a resource type."""
        if resource_type.name in cls._resource_types:
            # Check if this is the same resource definition
            existing_type = cls._resource_types[resource_type.name]
            if existing_type.fields == resource_type.fields and existing_type.field_order == resource_type.field_order:
                # Same resource definition - allow idempotent registration
                return
            else:
                raise ValueError(f"Resource type '{resource_type.name}' is already registered with different definition")

        cls._resource_types[resource_type.name] = resource_type

    @classmethod
    def get_resource_type(cls, name: str) -> ResourceType | None:
        """Get a resource type by name."""
        return cls._resource_types.get(name)

    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a resource type is registered."""
        return name in cls._resource_types

    @classmethod
    def list_resource_types(cls) -> list[str]:
        """List all registered resource type names."""
        return sorted(cls._resource_types.keys())

    @classmethod
    def create_resource_instance(cls, resource_name: str, values: dict[str, Any] | None = None) -> ResourceInstance:
        """Create a resource instance by type name."""
        resource_type = cls.get_resource_type(resource_name)
        if not resource_type:
            available_types = cls.list_resource_types()
            raise ValueError(f"Unknown resource type '{resource_name}'. Available types: {available_types}")

        # Create instance (no global tracking)
        instance = ResourceInstance(resource_type, values if values is not None else {})
        return instance

    @classmethod
    def clear(cls) -> None:
        """Clear all registered resource types (for testing)."""
        cls._resource_types.clear()
