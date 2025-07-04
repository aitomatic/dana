from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.rag.pipeline.rag_orchestrator import RAGOrchestrator
from dana.common.resource.rag.pipeline.unified_cache_manager import UnifiedCacheManager


class RAGResource(BaseResource):
    """RAG resource for document retrieval."""

    def __init__(
        self,
        sources: list[str],
        name: str = "rag_resource",
        cache_dir: str = ".cache/rag",
        force_reload: bool = False,
        description: str | None = None,
    ):
        super().__init__(name, description)
        self.sources = sources
        self.force_reload = force_reload
        self._cache_manager = UnifiedCacheManager(cache_dir)
        self._orchestrator = RAGOrchestrator(cache_manager=self._cache_manager)
        self._is_ready = False

    async def initialize(self) -> None:
        """Initialize and preprocess sources."""
        await super().initialize()
        self._orchestrator._preprocess(self.sources, self.force_reload)
        self._is_ready = True

    @ToolCallable.tool
    async def query(self, query: str, num_results: int = 10) -> str:
        """Retrieve relevant documents."""
        if not self._is_ready:
            await self.initialize()

        results = await self._orchestrator.retrieve(query, num_results)
        return "\n\n".join([result.node.get_content() for result in results])
