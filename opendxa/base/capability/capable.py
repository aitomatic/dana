"""Mixin for capable objects."""

from typing import Optional, List, Any, Dict
from opendxa.base.capability.base_capability import BaseCapability, CapabilityApplicationResult
from opendxa.common.mixins.tool_callable import ToolCallable


class CapabilityError(Exception):
    """Base class for capability-related errors."""
    pass


class CapabilityNotFoundError(CapabilityError):
    """Raised when a capability is not found."""
    pass


class CapabilityAlreadyExistsError(CapabilityError):
    """Raised when trying to add a duplicate capability."""
    pass


class Capable(ToolCallable):
    """Mixin for capable objects."""

    def __init__(self, capabilities: Optional[List[BaseCapability]] = None):
        """Initialize the Capable object.

        Args:
            capabilities: A list of BaseCapability objects.
        """
        super().__init__()  # Initialize ToolCallable first
        self._capabilities: List[BaseCapability] = capabilities or []

    def __contains__(self, capability: BaseCapability) -> bool:
        """Check if capability exists using 'in' operator.
        
        Args:
            capability: The capability to check for.
            
        Returns:
            True if the capability exists, False otherwise.
        """
        return capability in self._capabilities

    @property
    def capabilities(self) -> List[BaseCapability]:
        """Get the list of capabilities."""
        return self._capabilities.copy()

    @ToolCallable.tool
    def apply_capability(self, capability: BaseCapability, request: Optional[Dict[str, Any]] = None) -> CapabilityApplicationResult:
        """Apply a capability to the Capable object.

        Args:
            capability: The BaseCapability object to apply.
            request: The request to apply the capability to.

        Returns:
            CapabilityApplicationResult containing the result of applying the capability.
        """
        if not self.has_capability(capability):
            return CapabilityApplicationResult(
                success=False,
                result=request or {},
                error=CapabilityNotFoundError(f"Capability {capability.name} not found")
            )
        return capability.apply(request or {})

    def has_capability(self, capability: BaseCapability) -> bool:
        """Check if the Capable object has a specific capability.

        Args:
            capability: The BaseCapability object to check for.

        Returns:
            True if the Capable object has the capability, False otherwise.
        """
        return capability in self._capabilities

    def add_capability(self, capability: BaseCapability) -> None:
        """Add a capability to the Capable object.

        Args:
            capability: The BaseCapability object to add.

        Raises:
            CapabilityAlreadyExistsError: If the capability already exists.
        """
        if self.has_capability(capability):
            raise CapabilityAlreadyExistsError(f"Capability {capability.name} already exists")
        self._capabilities.append(capability)

    def remove_capability(self, capability: BaseCapability) -> None:
        """Remove a capability from the Capable object.

        Args:
            capability: The BaseCapability object to remove.

        Raises:
            CapabilityNotFoundError: If the capability does not exist.
        """
        if not self.has_capability(capability):
            raise CapabilityNotFoundError(f"Capability {capability.name} not found")
        self._capabilities.remove(capability)