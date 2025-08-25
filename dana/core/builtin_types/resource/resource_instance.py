"""
Resource Instance

Extends StructInstance to add resource-specific functionality while maintaining
compatibility with the struct system.
"""

from collections.abc import Callable
from typing import Any

from dana.core.builtin_types.struct_system import StructInstance

from .resource_type import ResourceType


# Default resource method implementations
def default_resource_start(resource_instance: "ResourceInstance") -> bool:
    """Default start method for resources."""
    return resource_instance.start()


def default_resource_stop(resource_instance: "ResourceInstance") -> bool:
    """Default stop method for resources."""
    return resource_instance.stop()


def default_resource_query(resource_instance: "ResourceInstance", request: dict[str, Any]) -> dict[str, Any]:
    """Default query method for resources."""
    return resource_instance.query(request)


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
        # Call parent constructor (import registry lazily to avoid circular import)
        from dana.registry import RESOURCE_REGISTRY

        super().__init__(resource_type, values or {}, RESOURCE_REGISTRY)

        # Resource-specific attributes for composition
        self._backend = None
        self._delegates = {}  # Name -> delegate object mapping

    @staticmethod
    def get_default_resource_fields() -> dict[str, str | dict[str, Any]]:
        """Get the default fields that all resources should have.

        This method defines what the standard resource fields are,
        keeping the definition close to where they're used.
        """
        return {
            "state": {
                "type": "str",
                "default": "CREATED",
                "comment": "Current state of the resource",
            }
        }

    @staticmethod
    def get_default_dana_methods() -> dict[str, Callable]:
        """Get the default resource methods that all resources should have.

        This method defines what the standard resource methods are,
        keeping the definition close to where they're implemented.
        """
        return {
            "start": default_resource_start,
            "stop": default_resource_stop,
            "query": default_resource_query,
        }

    @property
    def resource_type(self) -> ResourceType:
        """Get the resource type definition."""
        return self._type  # type: ignore

    def has_method(self, method_name: str) -> bool:
        """Check if this resource has a method through composition/delegation."""
        # Check current instance
        if hasattr(self, method_name):
            return True

        # Check resource type
        if self.resource_type.has_method(method_name):
            return True

        # Check backend if available
        if self._backend and hasattr(self._backend, method_name):
            return True

        # Check delegates
        for delegate in self._delegates.values():
            if hasattr(delegate, method_name):
                return True

        return False

    def call_method(self, method_name: str, *args, **kwargs) -> Any:
        """Call a method on this resource using composition/delegation."""
        # Try to call method directly on instance
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            if callable(method):
                return method(*args, **kwargs)

        # Try to delegate to backend if available
        if self._backend and hasattr(self._backend, method_name):
            method = getattr(self._backend, method_name)
            if callable(method):
                return method(*args, **kwargs)

        # Try to delegate to registered delegates
        for delegate in self._delegates.values():
            if hasattr(delegate, method_name):
                method = getattr(delegate, method_name)
                if callable(method):
                    return method(*args, **kwargs)

        raise AttributeError(f"Method '{method_name}' not found on resource '{self.resource_type.name}'")

    def set_backend(self, backend: Any) -> None:
        """
        Set a backend implementation for this resource.

        Args:
            backend: The backend object to delegate calls to
        """
        self._backend = backend

    def add_delegate(self, name: str, delegate: Any) -> None:
        """
        Add a delegate object for method dispatch.

        Args:
            name: Name for this delegate
            delegate: The delegate object
        """
        self._delegates[name] = delegate

    def remove_delegate(self, name: str) -> None:
        """
        Remove a delegate object.

        Args:
            name: Name of the delegate to remove
        """
        if name in self._delegates:
            del self._delegates[name]

    def get_delegate(self, name: str) -> Any | None:
        """
        Get a delegate by name.

        Args:
            name: Name of the delegate

        Returns:
            The delegate object or None if not found
        """
        return self._delegates.get(name)

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

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        """Query the resource with a request."""
        # Default implementation returns basic status and metadata
        return {
            "success": True,
            "state": self.state,
            "metadata": self.get_metadata(),
            "request": request,
        }

    def get_metadata(self) -> dict[str, Any]:
        """Get resource metadata."""
        return {
            "name": getattr(self, "name", ""),
            "kind": getattr(self, "kind", ""),
            "state": self.state,
            "type": self.resource_type.name,
            "fields": {name: getattr(self, name) for name in self.resource_type.field_order},
        }
