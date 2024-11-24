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
        """Initialize resource.
        
        Args:
            name: Name of the resource
            description: Optional description of what the resource provides
            config: Optional configuration for the resource
        """
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
        """Initialize the resource.
        
        Override this method to perform any necessary setup.
        """
        pass

    async def cleanup(self) -> None:
        """Clean up the resource.
        
        Override this method to perform any necessary cleanup.
        """
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
            ResourceUnavailableError: If resource is not available
            ResourceAccessError: If resource access fails
        """
        if not self.is_available:
            raise ResourceUnavailableError(
                f"Resource {self.name} is not available"
            )

    @abstractmethod
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this resource can handle the given request.
        
        Args:
            request: Request to check
            
        Returns:
            True if this resource can handle the request, False otherwise
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 