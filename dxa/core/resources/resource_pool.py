"""
This module provides a simple resource pool implementation
for managing resources of type BaseResource.
"""

from typing import Dict, TypeVar
from .base_resource import BaseResource

T = TypeVar('T', bound=BaseResource)

class ResourcePool:
    """Simple resource pool without over-engineering"""
    
    def __init__(self):
        self._resources: Dict[str, BaseResource] = {}
    
    async def get_resource(self, resource_id: str) -> BaseResource:
        """Retrieve a resource by its ID.

        Args:
            resource_id (str): The ID of the resource to retrieve.

        Raises:
            KeyError: If the resource with the given ID is not found.
        """
        if resource_id not in self._resources:
            raise KeyError(f"Resource {resource_id} not found")
        return self._resources[resource_id]
    
    async def add_resource(self, resource_id: str, resource: BaseResource) -> None:
        """Add a resource to the pool.

        Args:
            resource_id (str): The ID of the resource to add.
            resource (BaseResource): The resource to add.
        """
        if resource_id in self._resources:
            await self._resources[resource_id].cleanup()
        self._resources[resource_id] = resource
        await resource.initialize()
    
    async def cleanup(self) -> None:
        """Cleanup all resources"""
        for resource in self._resources.values():
            await resource.cleanup()
        self._resources.clear() 