from llama_index.core import Document, VectorStoreIndex
from llama_index.core.schema import NodeWithScore

from dana.common.mixins.loggable import Loggable
from dana.common.sys_resource.rag.pipeline.document_chunker import DocumentChunker
from dana.common.sys_resource.rag.pipeline.document_loader import DocumentLoader
from dana.common.sys_resource.rag.pipeline.index_builder import IndexBuilder
from dana.common.sys_resource.rag.pipeline.index_combiner import IndexCombiner
from dana.common.sys_resource.rag.pipeline.retriever import Retriever
from dana.common.sys_resource.rag.pipeline.unified_cache_manager import UnifiedCacheManager
from dana.common.sys_resource.embedding import get_default_embedding_model
from dana.common.utils.misc import Misc
from llama_index.core.vector_stores import MetadataFilters
import traceback

class RAGOrchestrator(Loggable):
    def __init__(
        self,
        loader: DocumentLoader | None = None,
        chunker: DocumentChunker | None = None,
        index_builder: IndexBuilder | None = None,
        index_combiner: IndexCombiner | None = None,
        cache_manager: UnifiedCacheManager | None = None,
        retriever_cls: type[Retriever] = Retriever,
        embedding_model = None,
    ):
        super().__init__()
        self.loader = loader if loader else DocumentLoader()
        self.chunker = chunker if chunker else DocumentChunker()
        self.index_builder = index_builder if index_builder else IndexBuilder()
        self.index_combiner = index_combiner if index_combiner else IndexCombiner()
        self.cache_manager = cache_manager if cache_manager else UnifiedCacheManager()
        self.embedding_model = embedding_model if embedding_model else get_default_embedding_model()
        self._retriever_cls = retriever_cls
        self._retriever = None

    def resolve_sources(self, sources: list[str]) -> list[str]:
        """Resolve sources to absolute paths."""
        return [self.loader.resolve_single_source(source) for source in sources]

    async def _async_preprocess(self, sources: list[str], force_reload: bool = False):
        """Preprocess sources with comprehensive caching strategy.

        This method implements a cache-first approach that:
        1. Checks for cached combined index first
        2. Uses cached documents and indices when available
        3. Only processes missing components
        4. Caches newly created components
        """
        sources = self.resolve_sources(sources)
        self.debug(f"Preprocessing {len(sources)} sources: {sources}")

        # Skip all cache checks if force_reload is True
        if not force_reload:
            # First check if we have a cached combined index for these exact sources
            combined_index = await self.cache_manager.get_combined_index(sources)
            if combined_index is not None:
                self.debug(f"Found cached combined index for sources: {sources}")
                self._retriever = self._retriever_cls.from_index(combined_index, embed_model=self.embedding_model)
                return

        # Check for cached individual components (skip if force_reload)
        if not force_reload:
            cached_docs_by_source = await self.cache_manager.get_docs_by_source(sources)
            cached_indices_by_source = await self.cache_manager.get_indicies_by_source(sources)
        else:
            self.debug("Force reload: bypassing all cache checks")
            cached_docs_by_source = {source: None for source in sources}
            cached_indices_by_source = {source: None for source in sources}

        # Filter out None values and convert to proper types
        docs_by_source: dict[str, list[Document]] = {}
        indices_by_source: dict[str, VectorStoreIndex] = {}

        # Initialize what needs to be loaded/processed
        sources_needing_docs = list(sources)  # Start with all sources
        sources_needing_indices = list(sources)  # Start with all sources

        # Process cached documents (skip if force_reload)
        if not force_reload:
            for source in sources:
                cached_docs = cached_docs_by_source.get(source)
                if cached_docs and all(doc is not None for doc in cached_docs):
                    # Filter out None documents and cast to proper type
                    valid_docs = [doc for doc in cached_docs if doc is not None]
                    docs_by_source[source] = valid_docs
                    # Remove from sources needing docs since we have valid cached docs
                    if source in sources_needing_docs:
                        sources_needing_docs.remove(source)

        # Process cached indices (skip if force_reload)
        if not force_reload:
            for source in sources:
                cached_index = cached_indices_by_source.get(source)
                if cached_index:
                    indices_by_source[source] = cached_index
                    # Remove from sources needing indices since we have valid cached index
                    if source in sources_needing_indices:
                        sources_needing_indices.remove(source)

        self.debug(f"Sources needing docs: {sources_needing_docs}")
        self.debug(f"Sources needing indices: {sources_needing_indices}")

        # Load missing documents
        if sources_needing_docs:
            self.debug(f"Loading documents for {len(sources_needing_docs)} sources")
            new_docs_by_source = await self.loader.load_sources(sources_needing_docs)
            docs_by_source.update(new_docs_by_source)
            # Cache newly loaded documents
            await self.cache_manager.set_docs_by_source(new_docs_by_source)

        # Process documents through chunker
        # NOTE: We don't need to chunk documents because LlamaIndex does it automatically under the hood.
        # if docs_by_source:
        #     self.debug(f"Chunking documents for {len(docs_by_source)} sources")
        #     docs_by_source = await self.chunker.chunk_documents(docs_by_source)

        # Build missing indices
        if sources_needing_indices:
            docs_for_indexing = {s: docs_by_source[s] for s in sources_needing_indices if s in docs_by_source}
            if docs_for_indexing:
                self.debug(f"Building indices for {len(docs_for_indexing)} sources")
                try:
                    new_indices_by_source = await self.index_builder.build_indices(docs_for_indexing, embed_model=self.embedding_model)
                except Exception as e:
                    self.error(f"Error building indices for {sources_needing_indices}: {e}")
                    self.error(f"{traceback.format_exc()}")
                    new_indices_by_source = {}
                indices_by_source.update(new_indices_by_source)
                # Cache newly built indices
                await self.cache_manager.set_indicies_by_source(new_indices_by_source)

        if not indices_by_source:
            # Instead of raising an exception, create a fallback empty index
            self.warning("No valid indices available for any source - creating empty index")
            from llama_index.core import VectorStoreIndex, Document

            # Create a dummy document to avoid completely empty index issues
            dummy_doc = Document(text="No documents found in the specified sources.", metadata={"source": "system", "type": "fallback"})
            fallback_index = VectorStoreIndex.from_documents([dummy_doc], embed_model=self.embedding_model)
            indices_by_source = {"fallback": fallback_index}
            docs_by_source = {"fallback": [dummy_doc]}

        # Combine indices
        self.debug(f"Combining {len(indices_by_source)} indices")
        combined_index = await self.index_combiner.combine_indices(indices_by_source, docs_by_source, embed_model=self.embedding_model)

        # Cache combined index (always cache, even with force_reload)
        await self.cache_manager.set_combined_index(sources, combined_index)

        # Create retriever
        self._retriever = self._retriever_cls.from_index(combined_index, embed_model=self.embedding_model)
        self.debug("Preprocessing completed successfully")

    def _preprocess(self, sources: list[str], force_reload: bool = False):
        """Preprocess sources with optional cache bypass.

        Args:
            sources: List of source identifiers
            force_reload: If True, bypass all caches and reprocess everything
        """
        if force_reload:
            self.debug("Force reload requested - bypassing caches")

        Misc.safe_asyncio_run(self._async_preprocess, sources, force_reload)

    async def retrieve(self, query: str, num_results: int = 10) -> list[NodeWithScore]:
        """Retrieve relevant documents for the given query.

        Args:
            query: Search query string
            num_results: Maximum number of results to return

        Returns:
            List of NodeWithScore objects containing relevant documents

        Raises:
            ValueError: If retriever is not initialized (call _preprocess first)
        """
        if self._retriever is None:
            raise ValueError("Retriever not initialized. Call _preprocess() with sources first.")
        return await self._retriever.aretrieve(query, num_results)

    async def retrieve_with_filters(self, query: str, num_results: int = 10, filters: MetadataFilters | None = None) -> list[NodeWithScore]:
        if filters is None:
            return await self.retrieve(query, num_results)
        return await self._retriever.aretrieve_with_filters(query, num_results, filters)
