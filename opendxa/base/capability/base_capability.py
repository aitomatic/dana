"""Base capability for DXA."""

from abc import ABC
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.mixins.configurable import Configurable


@dataclass
class CapabilityApplicationResult:
    """Result of applying a capability."""
    success: bool
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None


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

    def apply(self, request: Dict[str, Any]) -> CapabilityApplicationResult:
        """Apply this capability."""
        if not self._is_enabled:
            return CapabilityApplicationResult(success=False, result=request, error=f"Capability {self.name} is not enabled")
        return CapabilityApplicationResult(success=True, result=request, error=None)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if capability can handle request."""
        raise NotImplementedError
