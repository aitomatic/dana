"""Mixin for capable objects."""

from typing import Any

from pydantic import BaseModel, Field

from opendxa.common.capability.base_capability import BaseCapability, CapabilityApplicationResult
from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.types import BaseRequest


class CapabilityError(Exception):
    """Base class for capability-related errors."""

    pass


class CapabilityNotFoundError(CapabilityError):
    """Error raised when a capability is not found."""

    pass


class CapabilityRequest(BaseModel):
    """Request for applying a capability."""

    parameters: dict[str, Any] = Field(default_factory=dict)


class Capable:
    """Mixin for capable objects."""

    def __init__(self, capabilities: list[BaseCapability] | None = None):
        """Initialize the Capable object.

        Args:
            capabilities: A list of BaseCapability objects.
        """
        super().__init__()  # Initialize ToolCallable first
        self._capabilities: list[BaseCapability] = capabilities or []

    def __contains__(self, capability: BaseCapability) -> bool:
        """Check if capability exists using 'in' operator.

        Args:
            capability: The capability to check for.

        Returns:
            True if the capability exists, False otherwise.
        """
        return capability in self._capabilities

    @property
    def capabilities(self) -> list[BaseCapability]:
        """Get the list of capabilities."""
        return self._capabilities.copy()

    @ToolCallable.tool
    def apply_capability(self, capability: BaseCapability, request: BaseRequest | None = None) -> CapabilityApplicationResult:
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
                content=request.arguments if request else {},
                error=f"Capability {capability.name} not found",
            )

        # Create a BaseRequest if we don't have one
        if request is None:
            request = BaseRequest(arguments={})

        return capability.apply(request)

    def has_capability(self, capability: BaseCapability) -> bool:
        """Check if capability exists.

        Args:
            capability: The capability to check for.

        Returns:
            True if the capability exists, False otherwise.
        """
        return capability in self._capabilities

    def add_capability(self, capability: BaseCapability) -> None:
        """Add a capability to the Capable object.

        Args:
            capability: The capability to add.
        """
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
