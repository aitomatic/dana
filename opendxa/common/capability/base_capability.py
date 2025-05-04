"""Base capability for DXA."""

from abc import ABC
from typing import Any, Dict, Optional

from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.types import BaseRequest, BaseResponse


class CapabilityApplicationResult(BaseResponse):
    """Result of applying a capability."""

    pass


class BaseCapability(ABC, ToolCallable, Configurable):
    """Base class for agent capabilities."""

    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize capability.

        Args:
            name: Name of the capability
            description: Optional description of what the capability does
        """
        self.name = name
        self.description = description or "No description provided"
        self._is_enabled = True
        ToolCallable.__init__(self)
        Configurable.__init__(self)

    @property
    def is_enabled(self) -> bool:
        """Check if capability is currently enabled."""
        return self._is_enabled

    def enable(self):
        """Enable this capability."""
        self._is_enabled = True

    def disable(self):
        """Disable this capability."""
        self._is_enabled = False

    @ToolCallable.tool
    def apply(self, request: BaseRequest) -> CapabilityApplicationResult:
        """Apply this capability."""
        if not self._is_enabled:
            return CapabilityApplicationResult(success=False, content=request, error=f"Capability {self.name} is not enabled")
        return CapabilityApplicationResult(success=True, content=request, error=None)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if capability can handle request."""
        raise NotImplementedError
