"""Mixin for identifiable objects."""

from typing import Optional
import uuid


class Identifiable:
    """Mixin for identifiable objects."""

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """Initialize an identifiable object.
        
        Args:
            name: Optional name for the object
            description: Optional description of the object
        """
        self.id = str(uuid.uuid4())  # must have an id
        self.name = name or self.__class__.__name__  # must have a name
        self.description = description
