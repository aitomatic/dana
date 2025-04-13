"""Objects that have a registry for other objects"""

from typing import Dict, TypeVar, Generic, Any

RegistryObjectType = TypeVar('RegistryObjectType', bound=Any)

class Registerable(Generic[RegistryObjectType]):
    """Objects that have a registry for other objects"""
    def __init__(self):
        self._registry: Dict[str, RegistryObjectType] = {}

    def get_from_registry(self, object_id: str) -> RegistryObjectType:
        """Get a resource from the registry."""
        if object_id not in self._registry:
            raise ValueError(f"Object {object_id} not found in registry")
        return self._registry[object_id]
    
    def add_to_registry(self, object_id: str, the_object: RegistryObjectType) -> None:
        """Add an object to the registry with the specified ID.
        
        Args:
            object_id: Unique identifier for the object
            the_object: The object to register
        """
        self._registry[object_id] = the_object
    
    def remove_from_registry(self, object_id: str) -> None:
        """Remove an object from my registry."""
        del self._registry[object_id]
