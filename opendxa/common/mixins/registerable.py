"""Objects that have a registry for other objects"""

from typing import Dict, Type
from opendxa.common.mixins.identifiable import Identifiable

class Registerable(Identifiable):
    """Objects that have a class registry for members of the class."""

    # Class variable to store all registries by class
    _registries: Dict[Type['Registerable'], Dict[str, 'Registerable']] = {}

    @classmethod
    def _get_registry(cls) -> Dict[str, 'Registerable']:
        """Get the registry for this class.
        
        Returns:
            The registry dictionary for this class
        """
        if cls not in cls._registries:
            cls._registries[cls] = {}
        return cls._registries[cls]

    @classmethod
    def get_from_registry(cls, object_id: str) -> 'Registerable':
        """Get a resource from the registry."""
        registry = cls._get_registry()
        if object_id not in registry:
            raise ValueError(f"Object {object_id} not found in registry for {cls.__name__}")
        return registry[object_id]
    
    @classmethod
    def add_object_to_registry(cls, the_object: 'Registerable') -> None:
        """Add an object to the registry with the specified ID.
        
        Args:
            object_id: Unique identifier for the object
            the_object: The object to register
        """
        registry = cls._get_registry()
        registry[the_object.id] = the_object
    
    @classmethod    
    def remove_object_from_registry(cls, object_id: str) -> None:
        """Remove an object from my registry.
        
        First tries to remove from the given class's registry.
        If not found, scans all other registries to find and remove the object.
        
        Args:
            object_id: ID of the object to remove
        """
        # First try the given class's registry
        registry = cls._get_registry()
        if object_id in registry:
            del registry[object_id]
            return
            
        # If not found, scan all other registries
        for other_cls, other_registry in cls._registries.items():
            if other_cls != cls and object_id in other_registry:
                del other_registry[object_id]
                return
                
        raise ValueError(f"Object {object_id} not found in any registry")

    def add_to_registry(self) -> None:
        """Add myself to my registry."""
        self.__class__.add_object_to_registry(self)

    def remove_from_registry(self) -> None:
        """Remove myself from my registry."""
        self.__class__.remove_object_from_registry(self.id)
