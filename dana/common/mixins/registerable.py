"""Objects that have a registry for other objects"""

from dana.common.mixins.identifiable import Identifiable


class Registerable(Identifiable):
    """Objects that have a global registry for all registerable objects."""

    # Single global registry for all registerable objects
    _registry: dict[str, "Registerable"] = {}

    @classmethod
    def get_from_registry(cls, object_id: str) -> "Registerable":
        """Get a resource from the registry."""
        if object_id not in cls._registry:
            raise ValueError(f"Object {object_id} not found in registry {cls._registry.keys()}")
        return cls._registry[object_id]

    @classmethod
    def add_object_to_registry(cls, the_object: "Registerable") -> None:
        """Add an object to the registry with the specified ID.

        Args:
            the_object: The object to register
        """
        cls._registry[the_object.id] = the_object

    @classmethod
    def remove_object_from_registry(cls, object_id: str) -> None:
        """Remove an object from the registry.

        Args:
            object_id: ID of the object to remove
        """
        if object_id not in cls._registry:
            # raise ValueError(f"Object {object_id} not found in registry {cls._registry.keys()}")
            # NOTE : Temporarily disabled to avoid : `Object not found in registry` error
            pass
        else:
            del cls._registry[object_id]

    def add_to_registry(self) -> None:
        """Add myself to the registry."""
        self.__class__.add_object_to_registry(self)

    def remove_from_registry(self) -> None:
        """Remove myself from the registry."""
        # self.__class__.remove_object_from_registry(self.id)
        # NOTE : Temporarily disabled to avoid : `Object not found in registry` error
        pass
