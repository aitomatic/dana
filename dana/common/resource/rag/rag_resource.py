import os
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.rag.pipeline.rag_orchestrator import RAGOrchestrator
from dana.common.resource.rag.pipeline.unified_cache_manager import UnifiedCacheManager
from dana.common.utils.misc import Misc



class RAGResource(BaseResource):
    """RAG resource for document retrieval."""

    def __init__(
        self,
        sources: list[str],
        name: str = "rag_resource",
        cache_dir: str = None,  # Changed default to None
        force_reload: bool = False,
        description: str | None = None,
        debug: bool = True,
    ):
        super().__init__(name, description)
        self.sources = sources
        self.force_reload = force_reload
        self.debug = debug
        # Use DANAPATH if set, otherwise default to .cache/rag
        # if cache_dir is None:
        danapath = os.environ.get("DANAPATH")
        
        if danapath:
            if cache_dir:
                cache_dir = os.path.join(danapath, cache_dir)
            else:
                cache_dir = os.path.join(danapath, ".cache", 'rag')
        else:
            cache_dir = ".cache/rag"

        self._cache_manager = UnifiedCacheManager(cache_dir)
        self._orchestrator = RAGOrchestrator(cache_manager=self._cache_manager)
        self._is_ready = False
        self._filenames = None

    @property
    def filenames(self) -> list[str]:
        if not self._is_ready:
            Misc.safe_asyncio_run(self.initialize)
        return self._filenames

    async def initialize(self) -> None:
        """Initialize and preprocess sources."""
        await super().initialize()
        self._orchestrator._preprocess(self.sources, self.force_reload)
        self._is_ready = True
        self._filenames = self._orchestrator._retriever.get_all_filenames()

    @ToolCallable.tool
    async def query(self, query: str, num_results: int = 10) -> str:
        """Retrieve relevant documents."""
        if not self._is_ready:
            await self.initialize()

        if self.debug:
            print(f"Querying {num_results} results from {self.name} RAG with query: {query}")

        results = await self._orchestrator.retrieve(query, num_results)
        return "\n\n".join([result.node.get_content() for result in results])
