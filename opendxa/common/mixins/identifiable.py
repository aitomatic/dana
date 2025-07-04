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
        self.id = Misc.generate_uuid(8)
        self.name = name or self.__class__.__name__  # must have a name
        self.description = description
