from adana.common.base_wr import BaseWR
from adana.common.protocols import ResourceProtocol
from adana.core.global_registry import get_resource_registry


class BaseResource(BaseWR, ResourceProtocol):
    """This docstring is the public description of the resource.
    Here we place all the public descriptions an agent would need to know
    do use the resource effectively. This will go into the RESOURCE_DESCRIPTIONS
    section of the agent's system prompt.
    """

    def __init__(
        self, resource_type: str | None = None, resource_id: str | None = None, auto_register: bool = True, registry=None, **kwargs
    ):
        """
        Initialize the BaseResource.

        Args:
            resource_type: Type of resource (e.g., 'search', 'database')
            resource_id: ID of the resource (defaults to None)
            auto_register: Whether to automatically register with the global registry
            registry: Specific registry to use (defaults to global registry)
            **kwargs: Additional arguments passed to parent classes
        """
        # Call super().__init__ to properly initialize all parent classes
        super().__init__(object_id=resource_id, **kwargs)
        self.resource_type = resource_type or self.__class__.__name__

        # Handle resource registration
        self._registry = registry or get_resource_registry()
        if auto_register:
            self._register_self()

    # ============================================================================
    # RESOURCE REGISTRY MANAGEMENT
    # ============================================================================

    def _get_registry(self):
        """Get the resource registry."""
        return self._registry

    def _get_object_type(self) -> str:
        """Get the resource type for registry."""
        return self.resource_type

    def _get_capabilities(self) -> list[str]:
        """Get list of resource capabilities."""
        capabilities = []
        # Add resource type as capability
        capabilities.append(f"resource_type_{self.resource_type}")
        return capabilities

    def unregister_resource(self) -> bool:
        """
        Unregister this resource from the registry.

        Returns:
            True if successfully unregistered, False otherwise
        """
        return self._unregister_self()

    # ============================================================================
    # RESOURCE IDENTITY
    # ============================================================================

    @property
    def resource_id(self) -> str:
        """Get the resource id."""
        return self._object_id

    @resource_id.setter
    def resource_id(self, value: str):
        """Set the resource id."""
        self._object_id = value
