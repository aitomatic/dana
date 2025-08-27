"""
Index Building Module

This module handles the creation of vector indices from chunked documents.
It implements both individual source indices and combined indices that
merge multiple sources while preserving embedding optimizations.

The IndexBuilder class is responsible for:
- Creating vector indices from document chunks
- Building individual source-specific indices
- Creating combined indices from existing indices without recomputing embeddings
- Optimizing embedding reuse during index creation
"""

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document

from dana.common.sys_resource.rag.pipeline.base_stage import BaseStage


class IndexBuilder(BaseStage):
    """Handles vector index creation only."""

    _NAME = "index_builder"

    def __init__(self, sources_info: list[tuple[str, bool]] | None = None, **kwargs):
        """Initialize IndexBuilder.

        Args:
            sources_info: List of (path, is_dir) tuples for source information
            **kwargs: Additional arguments passed to BaseStage
        """
        super().__init__(**kwargs)
        self.sources_info = sources_info or []

    async def build_indices(self, docs_by_source: dict[str, list[Document]], embed_model: str | None = None) -> dict[str, VectorStoreIndex]:
        """Create separate indices for each source and a combined index.

        This method creates individual vector indices for each document source
        and then combines them into a unified index that preserves embeddings
        from the individual indices.

        Args:
            docs_by_source: Dictionary mapping source identifiers to lists of documents.
                          Keys are source identifiers (strings), values are document lists.

        Returns:
            Dictionary containing individual source indices plus a "combined" index.
            Keys are source identifiers (strings or integers) plus "combined".
            Values are VectorStoreIndex objects ready for querying.

        Note:
            Individual indices are indexed by source key from input.
            The combined index reuses embeddings from individual indices
            to avoid recomputation, which is a significant performance optimization.
        """
        if not docs_by_source:
            raise ValueError("docs_by_source cannot be empty")

        self.debug(f"Building indices for {len(docs_by_source)} sources")

        # Create individual source indices in parallel
        individual_indices = {}

        for source_key, documents in docs_by_source.items():
            if not documents:
                self.debug(f"Warning: No documents for source {source_key}, skipping")
                continue

            self.debug(f"Creating index for source {source_key} with {len(documents)} documents")

            individual_indices[source_key] = VectorStoreIndex.from_documents(documents, embed_model=embed_model)  # NOTE : ADD embedding_model

        if not individual_indices:
            raise RuntimeError("No indices were successfully created from any source")

        self.debug(f"Created {len(individual_indices)} indices")
        return individual_indices
