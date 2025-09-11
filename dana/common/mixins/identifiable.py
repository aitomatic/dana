"""Mixin for identifiable objects."""

from dana.common.utils.misc import Misc


class Identifiable:
    """Mixin for identifiable objects."""

    def __init__(self, name: str | None = None, description: str | None = None):
        """Initialize an identifiable object.

        Args:
            name: Optional name for the object
            description: Optional description of the object
        """
        self.id = Misc.generate_uuid(8) if (not hasattr(self, "id") or self.id is None) else self.id # must have an id
        self.name = (name or self.__class__.__name__) if (not hasattr(self, "name") or self.name is None) else self.name # must have a name
        self.description = description if (not hasattr(self, "description") or self.description is None) else self.description # must have a description
