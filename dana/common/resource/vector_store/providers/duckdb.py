"""
DuckDB vector store provider implementation.
"""

from llama_index.vector_stores.duckdb import DuckDBVectorStore
from llama_index.core.vector_stores.types import VectorStore

from dana.common.resource.vector_store.config import DuckDBConfig


class DuckDBProvider:
    """Provider for DuckDB vector store."""

    @staticmethod
    def create(config: DuckDBConfig, embed_dim: int) -> VectorStore:
        """Create DuckDB vector store instance.

        Args:
            config: DuckDB-specific configuration
            embed_dim: Embedding dimension

        Returns:
            Configured DuckDBVectorStore instance
        """
        print(f"  -> Initializing DuckDB store at: {config.path}/{config.filename}")

        return DuckDBVectorStore(
            database_name=config.filename,
            persist_dir=config.path,
            table_name=config.table_name,
            embed_dim=embed_dim,
        )

    @staticmethod
    def validate_config(config: DuckDBConfig) -> None:
        """Validate DuckDB configuration.

        Args:
            config: DuckDB configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validation is already done in DuckDBConfig.__post_init__
        pass
