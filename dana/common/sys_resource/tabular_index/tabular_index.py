"""
Clean TabularIndex implementation using dependency injection.

Key improvements:
- Receives fully-configured dependencies (no config creation/mutation)
- Single responsibility: focuses only on tabular data processing
- Clean separation of concerns
- Easy to test with mock dependencies
"""

import asyncio
import logging
import os
import time
from collections.abc import Callable
from typing import Any

import pandas as pd
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import Document

from dana.common.sys_resource.tabular_index.config import BatchSearchConfig, TabularConfig
from dana.common.sys_resource.vector_store import VectorStoreProviderProtocol

logger = logging.getLogger(__name__)


class TabularIndex:
    """Clean tabular index implementation with dependency injection.

    This class focuses solely on tabular data processing. All dependencies
    (embedding model, vector store) are injected, making it much easier to
    test and maintain.
    """

    def __init__(self, config: TabularConfig, embedding_model: BaseEmbedding, provider: VectorStoreProviderProtocol):
        """Initialize TabularIndex with injected dependencies.

        Args:
            config: Tabular processing configuration
            embedding_model: Fully configured embedding model
            provider: Vector store provider for lifecycle management (contains vector_store)
        """
        self.config = config
        self.embedding_model = embedding_model
        self.provider = provider
        self.index: VectorStoreIndex | None = None

    async def initialize(self) -> None:
        """Initialize tabular index following ADR-001 architecture."""
        logger.info("Initializing TabularIndex...")

        if self._should_rebuild():
            logger.info("Index rebuild required")
            self._validate_rebuild_preconditions()
            self.index = await self._rebuild_index()
        else:
            logger.info("Loading existing index")
            self.index = await self._load_existing_index()

        logger.info("TabularIndex initialization complete")

    def _should_rebuild(self) -> bool:
        """Determine if index rebuild is needed (ADR-001 core decision logic).

        Returns:
            True if rebuild is needed, False if existing index can be used
        """
        # Core ADR-001 decision logic:
        # IF force_reload = True: → Rebuild
        # ELSE IF vector_store_exists() AND has_data(): → Use existing
        # ELSE: → Rebuild (first time or empty store)

        if self.config.force_reload:
            logger.info("Rebuild triggered: force_reload=True")
            return True

        if not self._vector_store_exists():
            logger.info("Rebuild triggered: vector store does not exist")
            return True

        if not self._vector_store_has_data():
            logger.info("Rebuild triggered: vector store exists but has no data")
            return True

        logger.info("Using existing vector store (exists and has data)")
        return False

    def _validate_rebuild_preconditions(self) -> None:
        """Validate preconditions before rebuilding (ADR-001 safety checks).

        Raises:
            FileNotFoundError: If source data is not accessible
            ValueError: If configuration is invalid for rebuild
        """
        logger.debug("Validating rebuild preconditions...")

        # Check source data is accessible
        if not os.path.exists(self.config.source):
            raise FileNotFoundError(f"Source data not found: {self.config.source}")

        # Check source data is readable
        try:
            if self.config.source.endswith((".csv", ".parquet")):
                # Quick read test (just header)
                if self.config.source.endswith(".csv"):
                    pd.read_csv(self.config.source, nrows=0)
                else:
                    pd.read_parquet(self.config.source).head(0)
        except Exception as e:
            raise ValueError(f"Source data is not readable: {e}")

        # Validate embedding model is available
        if self.embedding_model is None:
            raise ValueError("Embedding model is not configured")

        # Validate vector store provider is configured
        if self.provider is None:
            raise ValueError("Vector store provider is not configured")

        logger.debug("Rebuild preconditions validated successfully")

    async def _rebuild_index(self) -> VectorStoreIndex:
        """Rebuild index from scratch (ADR-001 rebuild path).

        Returns:
            Newly built VectorStoreIndex
        """
        logger.info("Starting index rebuild...")

        # Drop existing vector store data if it exists
        self._drop_existing_vector_store()

        # Build new index
        return await self._build_index()

    async def _load_existing_index(self) -> VectorStoreIndex:
        """Load index from existing vector store (ADR-001 load existing path).

        Returns:
            VectorStoreIndex loaded from existing vector store
        """
        logger.info("Loading index from existing vector store...")

        try:
            # Create index from existing vector store without adding documents
            storage_context = StorageContext.from_defaults(vector_store=self.provider.vector_store)
            index = VectorStoreIndex([], storage_context=storage_context, embed_model=self.embedding_model)

            # Log statistics about loaded index
            row_count = self._get_vector_store_row_count()
            logger.info(f"Successfully loaded existing index with {row_count} embeddings")

            return index

        except Exception as e:
            logger.error(f"Failed to load existing index: {e}")
            logger.info("Falling back to rebuild...")
            return await self._rebuild_index()

    def _vector_store_exists(self) -> bool:
        """Check if vector store exists and is accessible.

        Returns:
            True if vector store exists, False otherwise
        """
        return self.provider.exists()

    def _vector_store_has_data(self) -> bool:
        """Check if vector store contains data.

        Returns:
            True if vector store has data, False otherwise
        """
        return self.provider.has_data()

    def _get_vector_store_row_count(self) -> int:
        """Get the number of rows/embeddings in the vector store.

        Returns:
            Number of rows in vector store, 0 if cannot determine
        """
        return self.provider.get_row_count()

    def _drop_existing_vector_store(self) -> None:
        """Drop/clear existing vector store data before rebuild.

        This ensures atomic rebuild - we only drop after validating we can rebuild.
        """
        self.provider.drop_data()

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

        print(f"Retrieving {num_results} results for query: '{query}'")
        nodes = await self.index.as_retriever(similarity_top_k=num_results).aretrieve(query)  # type: ignore
        return [{"text": node.text, "metadata": node.metadata} for node in nodes]

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

        result = await self.retrieve(query, top_k)

        if callback:
            callback(query, result)

        return {"query": query, "results": result}

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

        tasks = []
        for query in queries:
            tasks.append(self.single_search(query, batch_config.top_k, callback))

        results = await asyncio.gather(*tasks)

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
        logger.info(f"Building index from source: {self.config.source}")

        # Load and process data
        df = self._load_dataframe_from_source()
        logger.info(f"Loaded {len(df)} rows from source data")

        documents = await self._create_documents(df)
        logger.info(f"Created {len(documents)} documents for indexing")

        # Create index with injected dependencies - clean and simple!
        index = self._create_index(documents)
        logger.info("Index build completed successfully")

        return index

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

    async def _create_documents(self, df: pd.DataFrame) -> list[Document]:
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

            # Handle EagerPromise if returned from Dana function
            from dana.core.concurrency.base_promise import BasePromise

            if isinstance(embedding_text, BasePromise):
                embedding_text = await embedding_text.await_result()

            # Skip if embedding text is empty
            if not embedding_text:
                skipped_count += 1
                continue

            # Create metadata using configured constructor
            metadata = {}
            if self.config.metadata_constructor:
                metadata = self.config.metadata_constructor(row_dict)

                # Handle EagerPromise if returned from Dana function
                if isinstance(metadata, BasePromise):
                    metadata = await metadata.await_result()

            # Create document
            doc = Document(
                text=str(embedding_text).strip(),
                metadata=metadata,
                excluded_embed_metadata_keys=self.config.excluded_embed_metadata_keys,
            )
            documents.append(doc)

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} rows due to empty embedding text")
        logger.debug(f"Document creation complete: {len(documents)} documents from {len(df)} rows")
        return documents

    def _create_index(self, documents: list[Document]) -> VectorStoreIndex:
        """Create vector store index from documents.

        Args:
            documents: List of documents to index

        Returns:
            Created VectorStoreIndex
        """
        # Clean implementation - just use injected dependencies!
        storage_context = StorageContext.from_defaults(vector_store=self.provider.vector_store)

        logger.info(f"Building vector index from {len(documents)} documents...")

        # Ensure DuckDB table exists before adding documents (critical fix)
        try:
            if hasattr(self.provider.vector_store, "client") and hasattr(self.provider.vector_store, "table_name"):
                client = self.provider.vector_store.client
                table_name = self.provider.vector_store.table_name
                embed_dim = getattr(self.provider.vector_store, "embed_dim", 1024)

                # Check if table exists, create it if missing
                try:
                    client.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                except Exception:
                    # Table doesn't exist, create it manually
                    create_sql = f"""
                    CREATE TABLE {table_name} (
                        node_id VARCHAR PRIMARY KEY,
                        text VARCHAR,
                        embedding FLOAT[{embed_dim}],
                        metadata_ JSON
                    )
                    """
                    client.execute(create_sql)
                    logger.info(f"Created DuckDB table '{table_name}'")
        except Exception as e:
            logger.warning(f"Failed to initialize DuckDB table: {e}")

        t1 = time.time()

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, embed_model=self.embedding_model, show_progress=True
        )

        build_time = time.time() - t1
        logger.info("✅ Vector index built successfully!")
        logger.info(f"🕒 Index build time: {build_time:.2f}s")

        return index
