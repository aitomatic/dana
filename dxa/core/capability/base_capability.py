"""Base capability for DXA."""

from abc import ABC
from typing import Dict, Any, Optional

class BaseCapability(ABC):
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

    def use(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Use this capability."""
        raise NotImplementedError

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if capability can handle request."""
        raise NotImplementedError
  