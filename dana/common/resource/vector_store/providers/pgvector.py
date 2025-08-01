"""
PostgreSQL with pgvector extension provider implementation.
"""

from llama_index.core.vector_stores.types import VectorStore

from dana.common.resource.vector_store.config import PGVectorConfig


class PGVectorProvider:
    """Provider for PostgreSQL with pgvector extension."""

    @staticmethod
    def create(config: PGVectorConfig, embed_dim: int) -> VectorStore:
        """Create PGVector store instance.

        Args:
            config: PGVector-specific configuration
            embed_dim: Embedding dimension

        Returns:
            Configured PGVectorStore instance

        Raises:
            ImportError: If PGVectorStore package is not installed
        """
        try:
            from llama_index.vector_stores.postgres import PGVectorStore
        except ImportError:
            raise ImportError("PGVectorStore is not installed. " "Please install it with `pip install llama-index-vector-stores-postgres`")

        print(f"  -> Initializing PGVector store for database: {config.database}")
        print(f"  -> HNSW config: m={config.hnsw.m}, ef_construction={config.hnsw.ef_construction}")

        return PGVectorStore.from_params(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            schema_name=config.schema_name,
            table_name=config.table_name,
            embed_dim=embed_dim,
            use_halfvec=config.use_halfvec,
            hnsw_kwargs=config.hnsw.to_kwargs(),
            hybrid_search=config.hybrid_search,
        )

    @staticmethod
    def validate_config(config: PGVectorConfig) -> None:
        """Validate PGVector configuration.

        Args:
            config: PGVector configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validation is already done in PGVectorConfig.__post_init__
        pass
