"""
Basic Shared Object Space for Phase 1

Simple object sharing mechanism for Dana-Python integration.
"""

import weakref
from typing import Any


class SharedObjectSpace:
    """Basic shared object space for Phase 1."""

    def __init__(self):
        self._objects: dict[int, Any] = {}
        self._object_ids: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        self._next_id = 0

    def register_object(self, obj: Any) -> int:
        """Register object and return its ID."""
        if obj in self._object_ids:
            return self._object_ids[obj]

        obj_id = self._next_id
        self._next_id += 1

        self._objects[obj_id] = obj
        self._object_ids[obj] = obj_id

        return obj_id

    def get_object(self, obj_id: int) -> Any | None:
        """Get object by ID."""
        return self._objects.get(obj_id)

    def cleanup(self):
        """Clean up unreferenced objects."""
        # Objects automatically cleaned up by weakref
        self._objects = {obj_id: obj for obj_id, obj in self._objects.items() if obj in self._object_ids}

    def get_stats(self) -> dict[str, int]:
        """Get statistics about the shared space."""
        return {"total_objects": len(self._objects), "next_id": self._next_id}


# Global shared space
_shared_space = SharedObjectSpace()


def get_shared_space() -> SharedObjectSpace:
    """Get the global shared object space."""
    return _shared_space
