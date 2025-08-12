"""
Knowledge Base Resource

Provides structured knowledge storage and retrieval capabilities for Dana agents.
This is a simplified implementation that can be enhanced with system resource bridges if needed.
"""

from dataclasses import dataclass, field
from typing import Any

from dana.common.types import BaseResponse
from dana.core.resource import BaseResource, ResourceState


@dataclass
class KnowledgeBaseResource(BaseResource):
    """Knowledge base resource for structured knowledge storage."""

    kind: str = "knowledge_base"
    connection_string: str = "sqlite:///knowledge.db"

    # Internal knowledge storage
    _knowledge: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)

    def initialize(self) -> bool:
        """Initialize knowledge base resource."""
        print(f"Initializing knowledge base resource '{self.name}'")

        self.state = ResourceState.RUNNING
        self.capabilities = ["store", "retrieve", "delete"]
        print("Knowledge base resource initialized")
        return True

    def cleanup(self) -> bool:
        """Clean up knowledge base resource."""
        self._knowledge.clear()
        self.state = ResourceState.TERMINATED
        return True

    def query(self, request: Any) -> Any:
        """Query knowledge base system."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not running")

        if isinstance(request, dict):
            operation = request.get("operation", "retrieve")
            if operation == "store":
                key = request.get("key", "")
                value = request.get("value", "")
                metadata = request.get("metadata", {})
                return self.store(key, value, metadata)
            elif operation == "retrieve":
                key = request.get("key")
                query = request.get("query")
                return self.retrieve(key, query)
            elif operation == "delete":
                key = request.get("key", "")
                return self.delete(key)

        return BaseResponse(success=False, error="Invalid knowledge base operation")

    def store(self, key: str, value: str, metadata: dict | None = None) -> BaseResponse:
        """Store knowledge."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not running")

        self._knowledge[key] = {"value": value, "metadata": metadata if metadata is not None else {}, "created_at": "2025-01-01T00:00:00Z"}

        return BaseResponse(success=True, content={"message": "Knowledge stored"})

    def retrieve(self, key: str | None = None, query: str | None = None) -> BaseResponse:
        """Retrieve knowledge."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not running")

        if key:
            if key in self._knowledge:
                return BaseResponse(success=True, content=self._knowledge[key])
            else:
                return BaseResponse(success=False, error=f"Key '{key}' not found")
        elif query:
            results = []
            for k, v in self._knowledge.items():
                if query.lower() in k.lower() or query.lower() in v["value"].lower():
                    results.append({"key": k, **v})
            return BaseResponse(success=True, content={"results": results})
        else:
            return BaseResponse(success=True, content={"results": [{"key": k, **v} for k, v in self._knowledge.items()]})

    def delete(self, key: str) -> BaseResponse:
        """Delete knowledge."""
        if not self.is_running():
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not running")

        if key in self._knowledge:
            del self._knowledge[key]
            return BaseResponse(success=True, content={"message": "Knowledge deleted"})
        else:
            return BaseResponse(success=False, error=f"Key '{key}' not found")

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "name": self.name,
            "kind": self.kind,
            "state": self.state.value,
            "connection_string": self.connection_string,
            "capabilities": self.capabilities,
            "total_entries": len(self._knowledge),
        }


__all__ = ["KnowledgeBaseResource"]
