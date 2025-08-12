"""
Resource Instance

Extends StructInstance to add resource-specific functionality while maintaining
compatibility with the struct system.
"""

from typing import Any

from dana.core.lang.interpreter.struct_system import StructInstance

from .resource_type import ResourceType


class ResourceInstance(StructInstance):
    """
    Resource instance that extends StructInstance with resource-specific functionality.

    Resources are struct instances with additional lifecycle management capabilities.
    """

    def __init__(self, resource_type: ResourceType, values: dict[str, Any] | None = None):
        """
        Initialize a resource instance.

        Args:
            resource_type: The resource type definition
            values: Initial field values
        """
        # Call parent constructor
        super().__init__(resource_type, values or {})

        # Resource-specific attributes
        self._backend = None

    @property
    def resource_type(self) -> ResourceType:
        """Get the resource type definition."""
        return self._type

    def has_method(self, method_name: str) -> bool:
        """Check if this resource has a method (including inherited)."""
        # Check current instance
        if hasattr(self, method_name):
            return True

        # Check resource type
        if self.resource_type.has_method(method_name):
            return True

        return False

    def call_method(self, method_name: str, *args, **kwargs) -> Any:
        """Call a method on this resource with inheritance support."""
        # Try to call method directly
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            if callable(method):
                return method(*args, **kwargs)

        # Try to call method on parent instance
        if self.resource_type.parent_type:
            parent_instance = self._create_parent_instance()
            if hasattr(parent_instance, method_name):
                method = getattr(parent_instance, method_name)
                if callable(method):
                    return method(*args, **kwargs)

        raise AttributeError(f"Method '{method_name}' not found on resource '{self.resource_type.name}'")

    def _create_parent_instance(self) -> "ResourceInstance | None":
        """Create a parent instance for method calls."""
        if not self.resource_type.parent_type:
            return None

        # Create parent instance with current values
        parent_values = {}
        for field_name in self.resource_type.parent_type.field_order:
            if hasattr(self, field_name):
                parent_values[field_name] = getattr(self, field_name)

        return ResourceInstance(self.resource_type.parent_type, parent_values)

    def initialize(self) -> bool:
        """Initialize the resource."""
        try:
            self.state = "INITIALIZED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def cleanup(self) -> bool:
        """Clean up the resource."""
        try:
            self.state = "TERMINATED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def start(self) -> bool:
        """Start the resource."""
        try:
            self.state = "RUNNING"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def stop(self) -> bool:
        """Stop the resource."""
        try:
            self.state = "TERMINATED"
            return True
        except Exception as e:
            self.state = "ERROR"
            raise e

    def is_running(self) -> bool:
        """Check if the resource is running."""
        return self.state == "RUNNING"

    def get_metadata(self) -> dict[str, Any]:
        """Get resource metadata."""
        return {
            "name": getattr(self, "name", ""),
            "kind": getattr(self, "kind", ""),
            "state": self.state,
            "type": self.resource_type.name,
            "fields": {name: getattr(self, name) for name in self.resource_type.field_order},
        }
