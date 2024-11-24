"""Base capability for DXA."""

from abc import ABC, abstractmethod
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

    @abstractmethod
    async def use(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Use this capability.
        
        Args:
            context: Current context including any relevant state
            **kwargs: Additional arguments for specific capabilities
            
        Returns:
            Dict containing results of using the capability
        """
        pass

    @abstractmethod
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """Check if this capability can handle the given context.
        
        Args:
            context: Current context to check
            
        Returns:
            True if this capability can handle the context, False otherwise
        """
        pass 