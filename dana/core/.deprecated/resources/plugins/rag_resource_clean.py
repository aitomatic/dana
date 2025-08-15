"""
Clean RAG Resource - ResourceInstance version

Goes directly to dana.common.sys_resource.rag.rag_resource.RAGResource
instead of using BaseResource as intermediary.
"""

from typing import Any


def get_rag_resource_type():
    """Get the RAG ResourceType definition."""
    from dana.core.resource.resource_instance import ResourceType

    return ResourceType(
        name="RAGResource",
        fields={
            "name": "str",
            "sources": "list[str]",
            "cache_dir": "str",
            "chunk_size": "int",
            "chunk_overlap": "int",
            "reranking": "bool",
            "embedding_model": "str",
            "force_reload": "bool",
            "debug": "bool",
            "initial_multiplier": "int",
        },
        field_order=[
            "name",
            "sources",
            "cache_dir",
            "chunk_size",
            "chunk_overlap",
            "reranking",
            "embedding_model",
            "force_reload",
            "debug",
            "initial_multiplier",
        ],
        field_defaults={
            "sources": [],
            "cache_dir": ".cache/rag",
            "chunk_size": 1024,
            "chunk_overlap": 256,
            "reranking": False,
            "embedding_model": "default",
            "force_reload": False,
            "debug": False,
            "initial_multiplier": 2,
        },
        field_comments={},
    )


class RAGSysResourceBackend:
    """Backend adapter that connects ResourceInstance to sys_resource.RAGResource."""

    def __init__(self, resource_instance: Any):
        """Initialize the backend with ResourceInstance values."""
        self.resource_instance = resource_instance
        self._sys_rag: Any = None

    async def initialize(self) -> None:
        """Initialize the underlying RAG system resource."""
        from dana.common.sys_resource.rag.rag_resource import RAGResource

        # Extract values from ResourceInstance
        self._sys_rag = RAGResource(
            name=self.resource_instance.name,
            sources=self.resource_instance.sources,
            cache_dir=getattr(self.resource_instance, "cache_dir", ".cache/rag"),
            chunk_size=getattr(self.resource_instance, "chunk_size", 1024),
            chunk_overlap=getattr(self.resource_instance, "chunk_overlap", 256),
            reranking=getattr(self.resource_instance, "reranking", False),
            force_reload=getattr(self.resource_instance, "force_reload", False),
            debug=getattr(self.resource_instance, "debug", False),
            initial_multiplier=getattr(self.resource_instance, "initial_multiplier", 2),
        )

        # Initialize the sys resource
        await self._sys_rag.initialize()

    async def cleanup(self) -> None:
        """Clean up the RAG system resource."""
        if self._sys_rag:
            await self._sys_rag.cleanup()
            self._sys_rag = None

    async def query(self, request: Any) -> Any:
        """Query the RAG system."""
        if not self._sys_rag:
            raise RuntimeError("RAG resource not initialized")
        return await self._sys_rag.query(request)

    def get_stats(self) -> dict[str, Any]:
        """Get RAG statistics."""
        if not self._sys_rag:
            return {"error": "RAG resource not initialized"}
        return self._sys_rag.get_stats()

    def __getattr__(self, name: str) -> Any:
        """Delegate all other operations to the sys resource."""
        if self._sys_rag:
            return getattr(self._sys_rag, name)
        raise AttributeError(f"RAG resource not initialized, cannot access '{name}'")


def create_rag_resource(**kwargs):
    """Create a clean RAG ResourceInstance with direct sys_resource backend.

    This is the modern, clean way to create RAG resources.
    No BaseResource dependency - goes directly to dana.common.sys_resource.
    """
    from dana.core.resource.resource_factory import create_resource_instance

    # Get the ResourceType
    rag_resource_type = get_rag_resource_type()

    # Create the ResourceInstance
    instance = create_resource_instance(rag_resource_type, kwargs)

    # Attach the clean sys_resource backend
    backend = RAGSysResourceBackend(instance)
    instance.set_backend(backend)

    return instance


# For registration with resource factory
def register_clean_rag_resource():
    """Register the clean RAG resource type with the factory."""
    from dana.core.resource.resource_factory import register_resource_type

    rag_resource_type = get_rag_resource_type()

    # Register with factory using clean backend
    register_resource_type(rag_resource_type, backend_factory=lambda instance, config: RAGSysResourceBackend(instance))


# Export for backward compatibility
def RAGResource(**kwargs):
    """Create RAG resource (backward compatibility function name)."""
    return create_rag_resource(**kwargs)
