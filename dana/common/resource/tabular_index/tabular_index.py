"""
Clean TabularIndex implementation using dependency injection.

Key improvements:
- Receives fully-configured dependencies (no config creation/mutation)
- Single responsibility: focuses only on tabular data processing
- Clean separation of concerns
- Easy to test with mock dependencies
"""

from typing import Any
from collections.abc import Callable
import time
import pandas as pd

from llama_index.core.schema import Document
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from dana.common.resource.tabular_index.config import TabularConfig, BatchSearchConfig


class TabularIndex:
    """Clean tabular index implementation with dependency injection.

    This class focuses solely on tabular data processing. All dependencies
    (embedding model, vector store) are injected, making it much easier to
    test and maintain.
    """

    def __init__(self, config: TabularConfig, embedding_model: BaseEmbedding, vector_store: BasePydanticVectorStore):
        """Initialize TabularIndex with injected dependencies.

        Args:
            config: Tabular processing configuration
            embedding_model: Fully configured embedding model
            vector_store: Fully configured vector store
        """
        self.config = config
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.index: VectorStoreIndex | None = None

    async def initialize(self) -> None:
        """Initialize and build the tabular index."""
        await self._load_tabular_index()

    async def _load_tabular_index(self) -> None:
        """Load the tabular index from cache or rebuild if needed."""
        if self.config.force_reload:
            await self.reload_tabular_index()
        else:
            await self.load_tabular_index_from_cache()

    async def reload_tabular_index(self) -> None:
        """Reload the tabular index from the source."""
        self.index = await self._build_index()

    async def load_tabular_index_from_cache(self) -> None:
        """Load the tabular index from cache.

        TODO: Implement actual caching logic based on requirements.
        For now, just rebuild the index.
        """
        self.index = await self._build_index()

    async def retrieve(self, query: str, num_results: int = 10) -> list[dict[str, Any]]:
        """Retrieve documents based on query.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of retrieved documents with metadata
        """
        if not self.index:
            await self.initialize()

        # TODO: Implement actual retrieval logic
        print(f"Retrieving {num_results} results for query: {query}")
        return [{"placeholder": "result"}]

    async def single_search(
        self, query: str, top_k: int = 10, callback: Callable[[str, list[dict[str, Any]]], None] | None = None
    ) -> dict[str, Any]:
        """Perform single search operation.

        Args:
            query: Search query
            top_k: Number of top results to return
            callback: Optional callback for progress/results

        Returns:
            Search result
        """
        if not self.index:
            await self.initialize()

        # TODO: Implement actual single search logic
        result = {"query": query, "results": []}

        if callback:
            callback(query, result.get("results", []))

        return result

    async def batch_search(
        self,
        queries: list[str],
        batch_config: BatchSearchConfig,
        callback: Callable[[str, list[dict[str, Any]]], None] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform batch search operations.

        Args:
            queries: List of search queries
            batch_config: Batch processing configuration
            callback: Optional callback for progress/results

        Returns:
            List of search results
        """
        if not self.index:
            await self.initialize()

        # TODO: Implement actual batch search logic
        results = []
        for query in queries:
            result = await self.single_search(query, batch_config.top_k, callback)
            results.append(result)

        return results

    async def general_query(self, query: str, callback: Callable[[str, list[dict[str, Any]]], None] | None = None) -> list[dict[str, Any]]:
        """Perform general query operation.

        Args:
            query: General query
            callback: Optional callback for progress/results

        Returns:
            Query results
        """
        # TODO: Implement general query logic
        results = await self.retrieve(query)

        if callback:
            callback(query, results)

        return results

    async def _build_index(self) -> VectorStoreIndex:
        """Build the tabular index from source data.

        Returns:
            Built vector store index
        """
        print(f"Building index from source: {self.config.source}")

        # Load and process data
        df = self._load_dataframe_from_source()
        documents = self._create_documents(df)

        # Create index with injected dependencies - clean and simple!
        return self._create_index(documents)

    def _load_dataframe_from_source(self) -> pd.DataFrame:
        """Load dataframe from configured source.

        Returns:
            Loaded pandas DataFrame

        Raises:
            ValueError: If unsupported file type
        """
        source_path = self.config.source

        if source_path.endswith(".parquet"):
            return pd.read_parquet(source_path)
        elif source_path.endswith(".csv"):
            return pd.read_csv(source_path)
        else:
            raise ValueError(f"Unsupported file type: {source_path}")

    def _create_documents(self, df: pd.DataFrame) -> list[Document]:
        """Create LlamaIndex documents from DataFrame.

        Args:
            df: Source pandas DataFrame

        Returns:
            List of LlamaIndex Document objects
        """
        documents = []
        skipped_count = 0

        for _, row in df.iterrows():
            # Create embedding text using configured constructor
            row_dict = row.to_dict()
            embedding_text = self.config.embedding_field_constructor(row_dict)

            # Skip if embedding text is empty
            if not embedding_text:
                skipped_count += 1
                continue

            # Create metadata using configured constructor
            metadata = {}
            if self.config.metadata_constructor:
                metadata = self.config.metadata_constructor(row_dict)

            # Create document
            doc = Document(
                text=str(embedding_text).strip(),
                metadata=metadata,
                excluded_embed_metadata_keys=self.config.excluded_embed_metadata_keys,
            )
            documents.append(doc)

        if skipped_count > 0:
            print(f"Skipped {skipped_count} rows due to empty embedding text")

        print(f"Created {len(documents)} documents from {len(df)} rows")
        return documents

    def _create_index(self, documents: list[Document]) -> VectorStoreIndex:
        """Create vector store index from documents.

        Args:
            documents: List of documents to index

        Returns:
            Created VectorStoreIndex
        """
        # Clean implementation - just use injected dependencies!
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        print("Building vector index...")
        t1 = time.time()

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, embed_model=self.embedding_model, show_progress=True
        )

        build_time = time.time() - t1
        print("✅ Index built successfully!")
        print(f"\033[93m🕒 Index build time: {build_time:.2f}s\033[0m")

        return index
