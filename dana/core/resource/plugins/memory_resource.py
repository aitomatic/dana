"""
Memory Resource

Provides sophisticated memory management capabilities for Dana agents.
This is a simplified implementation that can be enhanced with system resource bridges if needed.
"""

from dataclasses import dataclass, field
from typing import Any

from dana.common.types import BaseResponse
from dana.core.resource import BaseResource, ResourceState


@dataclass
class MemoryResource(BaseResource):
    """Memory resource for sophisticated memory management."""

    kind: str = "memory"
    memory_type: str = "lt"  # lt, st, perm
    decay_rate: float = 0.1
    decay_interval: int = 3600

    # Internal memory storage
    _memories: dict[int, dict[str, Any]] = field(default_factory=dict, init=False)
    _next_id: int = field(default=1, init=False)

    def initialize(self) -> bool:
        """Initialize memory resource."""
        print(f"Initializing memory resource '{self.name}' with type '{self.memory_type}'")

        self.state = ResourceState.RUNNING
        self.capabilities = ["store", "retrieve", "update_importance"]
        print("Memory resource initialized")
        return True

    def cleanup(self) -> bool:
        """Clean up memory resource."""
        self._memories.clear()
        self._next_id = 1
        self.state = ResourceState.TERMINATED
        return True

    def query(self, request: Any) -> Any:
        """Query memory system."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Memory resource {self.name} not running")

        if isinstance(request, dict):
            operation = request.get("operation", "retrieve")
            if operation == "store":
                content = request.get("content", "")
                importance = request.get("importance", 1.0)
                context = request.get("context", {})
                return self.store(content, importance, context)
            elif operation == "retrieve":
                query = request.get("query", "")
                limit = request.get("limit", 10)
                return self.retrieve(query, limit)
            elif operation == "update_importance":
                memory_id = request.get("memory_id")
                importance = request.get("importance", 1.0)
                if memory_id is not None:
                    return self.update_importance(memory_id, importance)
                else:
                    return BaseResponse(success=False, error="memory_id is required")

        return BaseResponse(success=False, error="Invalid memory operation")

    def store(self, content: str, importance: float = 1.0, context: dict | None = None) -> BaseResponse:
        """Store memory."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Memory resource {self.name} not running")

        memory_id = self._next_id
        self._next_id += 1

        self._memories[memory_id] = {
            "content": content,
            "importance": importance,
            "context": context if context is not None else {},
            "created_at": "2025-01-01T00:00:00Z",
            "memory_type": self.memory_type,
        }

        return BaseResponse(success=True, content={"memory_id": memory_id, "message": "Memory stored"})

    def retrieve(self, query: str | None = None, limit: int = 10) -> BaseResponse:
        """Retrieve memory."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Memory resource {self.name} not running")

        memories = []
        for memory_id, memory in self._memories.items():
            if not query or query.lower() in memory["content"].lower():
                memories.append(
                    {
                        "id": memory_id,
                        "content": memory["content"],
                        "importance": memory["importance"],
                        "context": memory["context"],
                        "created_at": memory["created_at"],
                    }
                )

        # Sort by importance and limit
        memories.sort(key=lambda x: x["importance"], reverse=True)
        memories = memories[:limit]

        return BaseResponse(success=True, content={"memories": memories})

    def update_importance(self, memory_id: int, importance: float) -> BaseResponse:
        """Update memory importance."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Memory resource {self.name} not running")

        if memory_id not in self._memories:
            return BaseResponse(success=False, error=f"Memory {memory_id} not found")

        self._memories[memory_id]["importance"] = importance
        return BaseResponse(success=True, content={"message": "Importance updated"})

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        return {
            "name": self.name,
            "kind": self.kind,
            "memory_type": self.memory_type,
            "state": self.state.value,
            "decay_rate": self.decay_rate,
            "decay_interval": self.decay_interval,
            "capabilities": self.capabilities,
            "total_memories": len(self._memories),
            "average_importance": sum(m["importance"] for m in self._memories.values()) / len(self._memories) if self._memories else 0,
        }


__all__ = ["MemoryResource"]
