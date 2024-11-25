"""Base resource for DXA."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class ResourceError(Exception):
    """Base class for resource errors."""
    pass

class ResourceUnavailableError(ResourceError):
    """Error raised when resource is unavailable."""
    pass

class ResourceAccessError(ResourceError):
    """Error raised when resource access fails."""
    pass

class BaseResource(ABC):
    """Base class for agent resources."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize resource."""
        self.name = name
        self.description = description or "No description provided"
        self.config = config or {}
        self._is_available = True
        self.logger = logging.getLogger(f"{self.__class__.__name__}:{name}")

    @property
    def is_available(self) -> bool:
        """Check if resource is currently available."""
        return self._is_available

    async def initialize(self) -> None:
        """Initialize the resource."""
        pass

    async def cleanup(self) -> None:
        """Clean up the resource."""
        pass

    @abstractmethod
    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query this resource.
        
        Args:
            request: The request to send to the resource
            **kwargs: Additional arguments for specific resources
            
        Returns:
            Dict containing resource response
            
        Raises:
            ResourceAccessError: If resource access fails
        """
        pass

    @abstractmethod
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this resource can handle the given request."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 