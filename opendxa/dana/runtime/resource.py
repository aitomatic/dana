"""Resource management for DANA execution."""

from typing import Any, Dict, List

from opendxa.dana.common.exceptions import StateError


class ResourceRegistry:
    """Manages resources that can be accessed during DANA execution."""

    def __init__(self):
        """Initializes an empty resource registry."""
        self._resources: Dict[str, Any] = {}

    def register(self, name: str, resource: Any) -> None:
        """Register a resource with the given name.

        Args:
            name: The name to register the resource under
            resource: The resource object to register

        Raises:
            StateError: If the name is empty
        """
        if not name:
            raise StateError("Resource name cannot be empty")
        self._resources[name] = resource

    def get(self, name: str) -> Any:
        """Get a resource by name.

        Args:
            name: The name of the resource to get

        Returns:
            The registered resource

        Raises:
            StateError: If the resource is not found
        """
        if name not in self._resources:
            raise StateError(f"Resource not found: {name}")
        return self._resources[name]

    def list(self) -> List[str]:
        """List all registered resource names.

        Returns:
            A list of all registered resource names
        """
        return list(self._resources.keys())
