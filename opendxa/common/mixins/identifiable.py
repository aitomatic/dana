"""Mixin for identifiable objects."""

from typing import Optional
import uuid
from dataclasses import dataclass, field


@dataclass
class Identifiable:
    """Mixin for identifiable objects."""

    id: str = field(init=False)
    name: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Initialize the ID after dataclass initialization."""
        # self.id = str(uuid.uuid4())[:8]
        self.id = str(uuid.uuid4())
