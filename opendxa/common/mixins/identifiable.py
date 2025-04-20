"""Mixin for identifiable objects."""

from typing import Optional, Tuple
import uuid
from dataclasses import dataclass, field


class InvalidIdentifierStringError(Exception):
    """Raised when an identifier string is invalid."""
    pass


@dataclass
class Identifiable:
    """Mixin for identifiable objects."""

    id: str = field(init=False)
    name: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Initialize the ID after dataclass initialization."""
        self.id = str(uuid.uuid4())[:8]

    def get_name_id_function_string(self, function_name: str) -> str:
        """Get the name of the object as a string that can be used in a function call."""
        if self.name is None:
            raise ValueError("Name must be set before generating identifier string")
        if not function_name:
            raise ValueError("Function name cannot be empty")
        if "__" in function_name:
            raise ValueError("Function name cannot contain '__'")
        return f"{self.name}__{self.id}__{function_name}"
    
    def parse_name_id_function_string(self, string: str) -> Tuple[str, str, str]:
        """Parse the class, function, and ID from a string."""
        parts = string.split("__")
        if len(parts) != 3:
            raise InvalidIdentifierStringError(
                f"Expected 3 parts separated by '__', got {len(parts)} parts"
            )
        name, id_, function = parts
        if not all(parts):
            raise InvalidIdentifierStringError(
                "All parts must be non-empty"
            )
        return name, id_, function