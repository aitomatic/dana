"""
Clean factory classes for TabularIndex system components.

Follows single responsibility principle:
- EmbeddingFactory: Creates embedding models with proper dimension handling
- VectorStoreFactory: Creates vector stores with explicit parameters
"""

from typing import Any
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.vector_stores.types import VectorStore
from llama_index.vector_stores.duckdb import DuckDBVectorStore

from dana.common.resource.embedding.embedding_integrations import LlamaIndexEmbeddingResource
from dana.common.exceptions import EmbeddingError
from dana.common.resource.tabular_index.config import EmbeddingConfig, VectorStoreConfig


class EmbeddingFactory:
    """Factory for creating embedding models with proper dimension handling."""

    @staticmethod
    def create(config: EmbeddingConfig | None = None) -> tuple[BaseEmbedding, int]:
        """Create embedding model and return with actual dimensions.

        Args:
            config: Embedding configuration or None for defaults

        Returns:
            Tuple of (embedding_model, actual_dimensions)

        Raises:
            EmbeddingError: If embedding model creation fails
        """
        try:
            embedding_resource = LlamaIndexEmbeddingResource()

            if config:
                # Use specified configuration
                embedding_model = embedding_resource.get_embedding_model(config.model_name, config.dimensions)

                # Get actual dimensions
                if config.dimensions:
                    actual_dimensions = config.dimensions
                else:
                    actual_dimensions = EmbeddingFactory._extract_dimensions(embedding_model)
            else:
                # Use default from dana_config.json
                embedding_model = embedding_resource.get_default_embedding_model()
                actual_dimensions = EmbeddingFactory._extract_dimensions(embedding_model)

            return embedding_model, actual_dimensions

        except Exception as e:
            raise EmbeddingError(f"Failed to create embedding model: {e}") from e

    @staticmethod
    def _extract_dimensions(embedding_model: BaseEmbedding) -> int:
        """Extract dimensions from embedding model.

        Args:
            embedding_model: LlamaIndex BaseEmbedding instance

        Returns:
            Embedding dimension

        Raises:
            EmbeddingError: If dimension cannot be determined
        """
        # Strategy 1: Try to get from model object attributes
        if hasattr(embedding_model, "dimensions") and embedding_model.dimensions:
            return embedding_model.dimensions

        # Strategy 2: Generate a test embedding to get dimension
        try:
            test_embedding = embedding_model.get_text_embedding("test")
            return len(test_embedding)
        except Exception as e:
            raise EmbeddingError(f"Cannot determine embedding dimension: {e}")


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    def create(config: VectorStoreConfig, embed_dim: int) -> VectorStore:
        """Create vector store with explicit parameters.

        Args:
            config: Vector store configuration
            embed_dim: Embedding dimension (explicit parameter)

        Returns:
            Configured vector store instance

        Raises:
            ValueError: If unsupported provider or invalid configuration
        """
        if config.provider == "duckdb":
            return VectorStoreFactory._create_duckdb_store(config.storage_config, embed_dim)
        elif config.provider == "pgvector":
            return VectorStoreFactory._create_pgvector_store(config.storage_config, embed_dim)
        else:
            raise ValueError(f"Unsupported vector store provider: {config.provider}")

    @staticmethod
    def _create_duckdb_store(storage_config: dict[str, Any], embed_dim: int) -> DuckDBVectorStore:
        """Create DuckDB vector store."""
        # Set defaults for DuckDB configuration
        db_path = storage_config.get("path", ".cache/vector_db")
        db_filename = storage_config.get("filename", "vector_store.db")
        table_name = storage_config.get("table_name", "vectors")

        print(f"  -> Initializing DuckDB store at: {db_path}/{db_filename}")
        return DuckDBVectorStore(
            database_name=db_filename,
            persist_dir=db_path,
            table_name=table_name,
            embed_dim=embed_dim,
        )

    @staticmethod
    def _create_pgvector_store(storage_config: dict[str, Any], embed_dim: int) -> VectorStore:
        """Create PGVector store."""
        try:
            from llama_index.vector_stores.postgres import PGVectorStore
        except ImportError:
            raise ImportError("PGVectorStore is not installed. " "Please install it with `pip install llama-index-vector-stores-postgres`")

        # Extract PGVector configuration
        host = storage_config.get("host", "localhost")
        port = storage_config.get("port", 5432)
        database = storage_config.get("database", "vector_db")
        user = storage_config.get("user", "postgres")
        password = storage_config.get("password", "")
        schema_name = storage_config.get("schema_name", "public")
        table_name = storage_config.get("table_name", "vectors")

        # HNSW configuration
        hnsw_config = storage_config.get("hnsw", {})
        hnsw_kwargs = {
            "hnsw_m": hnsw_config.get("m", 64),
            "hnsw_ef_construction": hnsw_config.get("ef_construction", 400),
            "hnsw_ef_search": hnsw_config.get("ef_search", 400),
            "hnsw_dist_method": hnsw_config.get("dist_method", "vector_cosine_ops"),
        }

        print(f"  -> Initializing PGVector store for database: {database}")
        return PGVectorStore.from_params(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            schema_name=schema_name,
            table_name=table_name,
            embed_dim=embed_dim,
            use_halfvec=storage_config.get("use_halfvec", False),
            hnsw_kwargs=hnsw_kwargs,
            hybrid_search=storage_config.get("hybrid_search", False),
        )
