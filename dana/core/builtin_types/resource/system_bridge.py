"""
System Resource Bridge

This module provides bridges between system-level resources (dana.common.sys_resource)
and higher-level Dana resources (dana.core.builtin_types.resource). This allows sophisticated
system resources to be exposed through the standard Dana resource interface.

The bridge pattern enables:
1. Exposing sys resources through the Dana resource system
2. Maintaining the sophisticated functionality of sys resources
3. Providing a consistent interface for Dana agents
4. Allowing gradual migration of functionality
"""

from dataclasses import dataclass, field
from typing import Any

from dana.common.types import BaseRequest, BaseResponse
from dana.core.builtin_types.resource import BaseResource, ResourceState


@dataclass
class SystemResourceBridge(BaseResource):
    """Base bridge for system resources."""

    kind: str = "system_bridge"
    sys_resource_type: str = "unknown"
    _sys_resource: Any | None = field(default=None, init=False)

    def initialize(self) -> bool:
        """Initialize the bridge and underlying system resource."""
        print(f"Initializing system resource bridge '{self.name}' for {self.sys_resource_type}")

        try:
            self._sys_resource = self._create_sys_resource()
            if hasattr(self._sys_resource, "initialize") and self._sys_resource is not None:
                # Handle async initialization
                import asyncio

                if asyncio.iscoroutinefunction(self._sys_resource.initialize):
                    # For now, we'll handle this in the specific bridges
                    pass
                else:
                    self._sys_resource.initialize()

            self.state = ResourceState.RUNNING
            self.capabilities = self._get_capabilities()
            return True
        except Exception as e:
            print(f"Failed to initialize system resource bridge: {e}")
            return False

    def cleanup(self) -> bool:
        """Clean up the bridge and underlying system resource."""
        if self._sys_resource and hasattr(self._sys_resource, "cleanup"):
            if callable(self._sys_resource.cleanup):
                self._sys_resource.cleanup()

        self.state = ResourceState.TERMINATED
        return True

    def _create_sys_resource(self) -> Any:
        """Create the underlying system resource. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_sys_resource")

    def _get_capabilities(self) -> list[str]:
        """Get capabilities from the system resource. Override in subclasses."""
        return ["query"]


@dataclass
class LLMResourceBridge(SystemResourceBridge):
    """Bridge for LLM system resource."""

    kind: str = "llm"
    sys_resource_type: str = "llm"
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 1000

    def _create_sys_resource(self) -> Any:
        """Create LLM system resource."""
        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource

        return LegacyLLMResource(name=f"{self.name}_sys", model=self.model, temperature=self.temperature, max_tokens=self.max_tokens)

    def _get_capabilities(self) -> list[str]:
        """Get LLM capabilities."""
        return ["complete", "chat", "embed", "analyze"]

    def query(self, request: Any) -> Any:
        """Query the LLM system resource."""
        if not self.is_running() or not self._sys_resource:
            return BaseResponse(success=False, error=f"LLM bridge {self.name} not running")

        # Convert request to BaseRequest if needed
        if isinstance(request, str):
            # Simple text completion
            from dana.common.types import BaseRequest

            request = BaseRequest(operation="complete", arguments={"prompt": request})
        elif isinstance(request, dict):
            from dana.common.types import BaseRequest

            request = BaseRequest(operation=request.get("operation", "complete"), arguments=request)

        # Use the system resource's query method
        if hasattr(self._sys_resource, "query_sync"):
            response = self._sys_resource.query_sync(request)
        else:
            # Handle async query
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, need to handle this differently
                    # For now, return a placeholder
                    return BaseResponse(success=False, error="Async LLM queries not yet supported in bridge")
                else:
                    response = loop.run_until_complete(self._sys_resource.query(request))
            except Exception as e:
                return BaseResponse(success=False, error=f"LLM query failed: {e}")

        return response


@dataclass
class RAGResourceBridge(SystemResourceBridge):
    """Bridge for RAG system resource."""

    kind: str = "rag"
    sys_resource_type: str = "rag"
    sources: list[str] = field(default_factory=list)
    cache_dir: str | None = None
    chunk_size: int = 1024
    chunk_overlap: int = 256

    def _create_sys_resource(self) -> Any:
        """Create RAG system resource."""
        from dana.common.sys_resource.rag.rag_resource import RAGResource

        return RAGResource(
            sources=self.sources,
            name=f"{self.name}_sys",
            cache_dir=self.cache_dir if self.cache_dir is not None else "",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def _get_capabilities(self) -> list[str]:
        """Get RAG capabilities."""
        return ["query", "search", "summarize"]

    def query(self, request: Any) -> Any:
        """Query the RAG system resource."""
        if not self.is_running() or not self._sys_resource:
            return BaseResponse(success=False, error=f"RAG bridge {self.name} not running")

        # Extract query from request
        if isinstance(request, str):
            query_text = request
        elif isinstance(request, dict):
            query_text = request.get("query", "")
        elif isinstance(request, BaseRequest):
            query_text = request.arguments.get("query", "")
        else:
            return BaseResponse(success=False, error="Invalid request format")

        if not query_text:
            return BaseResponse(success=False, error="No query provided")

        # Use the system resource's query method
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, need to handle this differently
                return BaseResponse(success=False, error="Async RAG queries not yet supported in bridge")
            else:
                response = loop.run_until_complete(self._sys_resource.query(query_text))
                return BaseResponse(success=True, content=response)
        except Exception as e:
            return BaseResponse(success=False, error=f"RAG query failed: {e}")


# Memory, Knowledge Base, and Coding bridges removed - now using core plugins directly


# Factory function for creating bridges
def create_system_resource_bridge(resource_type: str, **kwargs) -> SystemResourceBridge:
    """Create a system resource bridge based on type."""
    if resource_type == "llm":
        return LLMResourceBridge(**kwargs)
    elif resource_type == "rag":
        return RAGResourceBridge(**kwargs)
    else:
        raise ValueError(f"Unknown system resource type: {resource_type}")


__all__ = [
    "SystemResourceBridge",
    "LLMResourceBridge",
    "RAGResourceBridge",
    "create_system_resource_bridge",
]
