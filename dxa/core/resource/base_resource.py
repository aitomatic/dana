"""Base resource implementation for DXA.

This module provides the foundational resource class that defines the interface
and common functionality for all DXA resources. Resources are managed entities
that provide specific capabilities to the system.

Classes:
    ResourceError: Base exception class for resource-related errors
    ResourceUnavailableError: Error raised when a resource cannot be accessed
    ResourceAccessError: Error raised when resource access is denied
    BaseResource: Abstract base class for all resources

Example:
    class CustomResource(BaseResource):
        async def initialize(self):
            # Resource-specific initialization
            pass

        async def cleanup(self):
            # Resource-specific cleanup
            pass
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import logging
from dataclasses import dataclass

class ResourceError(Exception):
    """Base class for resource errors."""
    pass

class ResourceUnavailableError(ResourceError):
    """Error raised when resource is unavailable."""
    pass

class ResourceAccessError(ResourceError):
    """Error raised when resource access fails."""
    pass

@dataclass
class ResourceConfig:
    """Base configuration for all resources."""
    name: str
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ResourceConfig':
        """Create config from dictionary."""
        return cls(**{
            k: v for k, v in config_dict.items() 
            # pylint: disable=no-member
            if k in cls.__dataclass_fields__
        })

@dataclass
class ResourceResponse:
    """Base response for all resources."""
    success: bool = True
    error: Optional[str] = None

class BaseResource(ABC):
    """Abstract base resource."""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        resource_config: Optional[Union[Dict[str, Any], ResourceConfig]] = None
    ):
        """Initialize resource.
        
        Args:
            name: Resource name
            description: Optional resource description
            config: Either a ResourceConfig object or a dict that can be converted to one
        """
        if isinstance(resource_config, dict):
            self.config = ResourceConfig.from_dict(resource_config)
        elif isinstance(resource_config, ResourceConfig):
            self.config = resource_config
        else:
            self.config = ResourceConfig(name=name, description=description)
            
        self.name = name or self.config.name
        self.description = self.config.description or "No description provided"
        self._is_available = False  # will only be True after initialization
        self.logger = logging.getLogger(f"{self.__class__.__name__}:{name}")

    @property
    def is_available(self) -> bool:
        """Check if resource is currently available."""
        return self._is_available

    async def initialize(self) -> None:
        """Initialize the resource."""
        self._is_available = True

    @abstractmethod
    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Query the resource."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resource."""
        pass

    # pylint: disable=unused-argument
    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request can be handled."""
        return False
        
    async def __aenter__(self) -> 'BaseResource':
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup() 