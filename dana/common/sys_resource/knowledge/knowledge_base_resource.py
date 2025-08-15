"""
Knowledge Base System Resource

BaseSysResource implementation for knowledge storage and retrieval.
This provides the backend functionality for knowledge base resources.
"""

from typing import Any
from dana.common.types import BaseRequest, BaseResponse
from dana.common.sys_resource.base_sys_resource import BaseSysResource


class KnowledgeBaseResource(BaseSysResource):
    """Knowledge base system resource for structured knowledge storage."""

    def __init__(self, name: str, connection_string: str = "sqlite:///knowledge.db", **kwargs):
        """Initialize knowledge base resource.

        Args:
            name: Resource name
            connection_string: Database connection string
            **kwargs: Additional configuration
        """
        super().__init__(name, description="Knowledge base for structured storage", config=kwargs)
        self.connection_string = connection_string
        self._knowledge: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize knowledge base resource."""
        self.info(f"Initializing knowledge base resource '{self.name}'")
        await super().initialize()
        self.info("Knowledge base resource initialized")

    async def cleanup(self) -> None:
        """Clean up knowledge base resource."""
        self._knowledge.clear()
        await super().cleanup()

    async def query(self, request: BaseRequest) -> BaseResponse:
        """Query knowledge base system."""
        if not self.is_available:
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not available")

        try:
            # Handle different request formats
            if hasattr(request, "arguments") and isinstance(request.arguments, dict):
                args = request.arguments
            elif isinstance(request, dict):
                args = request
            else:
                args = {"operation": "retrieve"}

            operation = args.get("operation", "retrieve")

            if operation == "store":
                key = args.get("key", "")
                value = args.get("value", "")
                metadata = args.get("metadata", {})
                return await self._store(key, value, metadata)
            elif operation == "retrieve":
                key = args.get("key")
                query_text = args.get("query")
                return await self._retrieve(key, query_text)
            elif operation == "delete":
                key = args.get("key", "")
                return await self._delete(key)
            else:
                return BaseResponse(success=False, error=f"Unknown operation: {operation}")

        except Exception as e:
            self.error(f"Knowledge base query failed: {e}")
            return BaseResponse(success=False, error=str(e))

    async def _store(self, key: str, value: str, metadata: dict | None = None) -> BaseResponse:
        """Store knowledge."""
        if not self.is_available:
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not available")

        self._knowledge[key] = {"value": value, "metadata": metadata if metadata is not None else {}, "created_at": "2025-01-01T00:00:00Z"}

        self.info(f"Stored knowledge for key: {key}")
        return BaseResponse(success=True, content={"message": "Knowledge stored"})

    async def _retrieve(self, key: str | None = None, query: str | None = None) -> BaseResponse:
        """Retrieve knowledge."""
        if not self.is_available:
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not available")

        if key:
            if key in self._knowledge:
                self.info(f"Retrieved knowledge for key: {key}")
                return BaseResponse(success=True, content=self._knowledge[key])
            else:
                return BaseResponse(success=False, error=f"Key '{key}' not found")
        elif query:
            results = []
            for k, v in self._knowledge.items():
                if query.lower() in k.lower() or query.lower() in v["value"].lower():
                    results.append({"key": k, **v})
            self.info(f"Query '{query}' returned {len(results)} results")
            return BaseResponse(success=True, content={"results": results})
        else:
            # Return all knowledge
            results = [{"key": k, **v} for k, v in self._knowledge.items()]
            self.info(f"Retrieved all knowledge: {len(results)} entries")
            return BaseResponse(success=True, content={"results": results})

    async def _delete(self, key: str) -> BaseResponse:
        """Delete knowledge."""
        if not self.is_available:
            return BaseResponse(success=False, error=f"Knowledge base resource {self.name} not available")

        if key in self._knowledge:
            del self._knowledge[key]
            self.info(f"Deleted knowledge for key: {key}")
            return BaseResponse(success=True, content={"message": "Knowledge deleted"})
        else:
            return BaseResponse(success=False, error=f"Key '{key}' not found")

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "name": self.name,
            "description": self.description,
            "is_available": self.is_available,
            "connection_string": self.connection_string,
            "total_entries": len(self._knowledge),
        }
