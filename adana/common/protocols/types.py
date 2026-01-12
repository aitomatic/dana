from abc import ABC
from enum import Enum
from typing import Any
import uuid


DictParams = dict[str, Any]


class LearningPhase(Enum):
    ACQUISITIVE = "ACQUISITIVE"  # initial learning/trial-level plasticity
    EPISODIC = "EPISODIC"  # episodic/hippocampal binding of information
    INTEGRATIVE = "INTEGRATIVE"  # offline replay, integration into cortex
    RETENTIVE = "RETENTIVE"  # long-term maintenance, habit formation


class Identifiable(ABC):
    """Base class for identifiable objects."""

    def __init__(self, object_id: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._object_id = object_id or str(uuid.uuid4())

    @property
    def object_id(self) -> str:
        """Get the id of the object."""
        if not hasattr(self, "_object_id"):
            self._object_id = str(uuid.uuid4())
        return self._object_id

    @object_id.setter
    def object_id(self, value: str):
        """Set the id of the object."""
        self._object_id = value
