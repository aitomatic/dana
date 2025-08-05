import os
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.resource.base_resource import BaseResource
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.resource.rag.pipeline.rag_orchestrator import RAGOrchestrator
from dana.common.resource.rag.pipeline.knowledge_loader import KnowledgeLoader
from dana.common.resource.rag.pipeline.unified_cache_manager import UnifiedCacheManager
from dana.common.types import BaseRequest
from dana.common.utils.misc import Misc
from llama_index.core import Settings
from dana.common.resource.rag.rag_resource import RAGResource
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

class KnowledgeResource(RAGResource):
    """RAG resource for document retrieval."""

    def __init__(
        self,
        sources: list[str],
        name: str = "knowledge_resource",
        cache_dir: str = None,  # Changed default to None
        force_reload: bool = False,
        description: str | None = None,
        chunk_size: int = 1024,
        chunk_overlap: int = 256,
        debug: bool = True,
        reranking: bool = False,
        initial_multiplier: int = 2,
    ):
        super().__init__(sources=sources, name=name, cache_dir=cache_dir, force_reload=force_reload, description=description, chunk_size=chunk_size, chunk_overlap=chunk_overlap, debug=debug, reranking=reranking, initial_multiplier=initial_multiplier)

    def post_init(self, sources: list[str], name: str, cache_dir: str, force_reload: bool, chunk_size: int, chunk_overlap: int, debug: bool, reranking: bool, initial_multiplier: int):
        Settings.chunk_size = chunk_size
        Settings.chunk_overlap = chunk_overlap
        self.sources = sources
        self.force_reload = force_reload
        self.debug = debug
        self.reranking = reranking
        self.initial_multiplier = initial_multiplier
        # Use DANAPATH if set, otherwise default to .cache/rag
        # if cache_dir is None:
        danapath = os.environ.get("DANAPATH")

        if danapath:
            if cache_dir:
                cache_dir = os.path.join(danapath, cache_dir)
            else:
                cache_dir = os.path.join(danapath, ".cache", "rag")
        else:
            cache_dir = ".cache/rag"

        self._cache_manager = UnifiedCacheManager(cache_dir)
        self._orchestrator = RAGOrchestrator(cache_manager=self._cache_manager, loader=KnowledgeLoader())
        self._is_ready = False
        self._filenames = None

        # Initialize LLM resource for reranking if enabled
        if self.reranking:
            self._llm_reranker = LLMResource(
                name=f"{name}_reranker",
                temperature=0.0,  # Use deterministic settings for reranking
            )
        else:
            self._llm_reranker = None

    @ToolCallable.tool
    async def get_facts(self, query: str, num_results: int = 3) -> str:
        """@description: Get existing facts from knowledge base
        """
        if not self._is_ready:
            await self.initialize()
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key="facts", operator=FilterOperator.NE, value=""),
            ]
        )
        results = await self._orchestrator.retrieve_with_filters(query, num_results, filters)
        results = [self.post_retrieve_process(result, "facts") for result in results]
        # Apply LLM reranking if enabled
        results = await self._apply_reranking(results, query, num_results)
        return  self._create_final_result(results)
    
    @ToolCallable.tool
    async def get_plan(self, query: str, num_results: int = 3) -> str:
        """@description: Get existing plan from knowledge base
        """
        if not self._is_ready:
            await self.initialize()
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key="plan", operator=FilterOperator.NE, value=""),
            ]
        )
        results = await self._orchestrator.retrieve_with_filters(query, num_results, filters)
        results = [self.post_retrieve_process(result, "plan") for result in results]
        results = await self._apply_reranking(results, query, num_results)
        return  self._create_final_result(results)
    
    @ToolCallable.tool
    async def get_heuristics(self, query: str, num_results: int = 3) -> str:
        """@description: Get existing heuristics from knowledge base
        """
        if not self._is_ready:
            await self.initialize()
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key="heuristics", operator=FilterOperator.NE, value=""),
            ]
        )
        results = await self._orchestrator.retrieve_with_filters(query, num_results, filters)
        results = [self.post_retrieve_process(result, "heuristics") for result in results]
        results = await self._apply_reranking(results, query, num_results)
        return  self._create_final_result(results)
    
    def post_retrieve_process(self, result: NodeWithScore, metadata_field_as_text : str | None = None) -> NodeWithScore:
        if metadata_field_as_text is not None:
            result.node.text = result.node.metadata[metadata_field_as_text]
        return result
    
    def _create_final_result(self, results: list[NodeWithScore]) -> str:
        return "\n\n".join([f"Source : {result.node.metadata['source']}\nContent : \n{result.get_content()}" for result in results])

    async def _apply_reranking(self, results: list[NodeWithScore], query: str, num_results: int) -> list[NodeWithScore]:
        if self.reranking and self._llm_reranker and len(results) > 1:
            results = await self._rerank_with_llm(query, results, num_results)
        elif len(results) > num_results:
            # Truncate to requested number if no reranking
            results = results[:num_results]
        return results
    
    async def query(self, query: str, num_results: int = 10) -> str:
        pass
    


if __name__ == "__main__":
    import asyncio
    async def main():
        knowledge_resource = KnowledgeResource(sources=["agents/financial_stmt_analysis/knows/processed_knowledge"], force_reload=True)
        await knowledge_resource.initialize()
        res = await knowledge_resource.get_plan("What is the capital expenditure for the company?", num_results=10)
        print(res)
    asyncio.run(main())

    