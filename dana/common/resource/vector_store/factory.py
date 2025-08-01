"""
Standardized factory for creating vector store instances.

This factory provides a clean, consistent interface for creating vector stores
across the entire codebase with proper provider abstraction.
"""

from typing import Any
from llama_index.core.vector_stores.types import VectorStore

from .config import VectorStoreConfig, create_duckdb_config, create_pgvector_config
from .providers import DuckDBProvider, PGVectorProvider


class VectorStoreFactory:
    """Standardized factory for creating vector store instances.

    This factory provides multiple creation methods to support different use cases
    while maintaining a consistent interface across the codebase.
    """

    @staticmethod
    def create(config: VectorStoreConfig, embed_dim: int) -> VectorStore:
        """Create vector store from structured configuration.

        Args:
            config: Structured vector store configuration
            embed_dim: Embedding dimension

        Returns:
            Configured vector store instance

        Raises:
            ValueError: If unsupported provider or invalid configuration
        """
        if config.provider == "duckdb":
            provider_config = config.duckdb
            DuckDBProvider.validate_config(provider_config)
            return DuckDBProvider.create(provider_config, embed_dim)

        elif config.provider == "pgvector":
            provider_config = config.pgvector
            PGVectorProvider.validate_config(provider_config)
            return PGVectorProvider.create(provider_config, embed_dim)

        else:
            raise ValueError(f"Unsupported vector store provider: {config.provider}")

    @staticmethod
    def create_from_dict(provider: str, embed_dim: int, **kwargs) -> VectorStore:
        """Create vector store from provider name and keyword arguments.

        This method provides a simplified interface for quick vector store creation.

        Args:
            provider: Vector store provider name ("duckdb" or "pgvector")
            embed_dim: Embedding dimension
            **kwargs: Provider-specific configuration parameters

        Returns:
            Configured vector store instance

        Raises:
            ValueError: If unsupported provider or invalid configuration

        Examples:
            # DuckDB
            store = VectorStoreFactory.create_from_dict(
                "duckdb",
                embed_dim=1536,
                path=".cache/my_vectors",
                filename="my_store.db"
            )

            # PGVector
            store = VectorStoreFactory.create_from_dict(
                "pgvector",
                embed_dim=1536,
                host="localhost",
                database="my_db",
                m=32,
                ef_construction=200
            )
        """
        if provider == "duckdb":
            config = create_duckdb_config(**kwargs)
        elif provider == "pgvector":
            config = create_pgvector_config(**kwargs)
        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")

        return VectorStoreFactory.create(config, embed_dim)

    @staticmethod
    def create_from_legacy_dict(config_dict: dict[str, Any], embed_dim: int) -> VectorStore:
        """Create vector store from legacy dictionary configuration.

        This method provides backward compatibility with the old configuration format
        used by tabular_index and other existing modules.

        Args:
            config_dict: Legacy configuration dictionary with nested structure
            embed_dim: Embedding dimension

        Returns:
            Configured vector store instance

        Example:
            config = {
                "provider": "duckdb",
                "storage_config": {
                    "path": ".cache/vectors",
                    "filename": "store.db",
                    "table_name": "vectors"
                }
            }
            store = VectorStoreFactory.create_from_legacy_dict(config, 1536)
        """
        provider = config_dict.get("provider", "duckdb")
        storage_config = config_dict.get("storage_config", {})

        if provider == "duckdb":
            config = create_duckdb_config(
                path=storage_config.get("path", ".cache/vector_db"),
                filename=storage_config.get("filename", "vector_store.db"),
                table_name=storage_config.get("table_name", "vectors"),
            )
        elif provider == "pgvector":
            # Extract HNSW config from nested structure
            hnsw_config = storage_config.get("hnsw", {})
            config_kwargs = {**storage_config}
            config_kwargs.update(hnsw_config)  # Flatten HNSW config
            config_kwargs.pop("hnsw", None)  # Remove nested hnsw dict
            config = create_pgvector_config(**config_kwargs)
        else:
            raise ValueError(f"Unsupported vector store provider: {provider}")

        return VectorStoreFactory.create(config, embed_dim)

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported vector store providers.

        Returns:
            List of supported provider names
        """
        return ["duckdb", "pgvector"]

    @staticmethod
    def validate_provider(provider: str) -> bool:
        """Validate if a provider is supported.

        Args:
            provider: Provider name to validate

        Returns:
            True if provider is supported, False otherwise
        """
        return provider in VectorStoreFactory.get_supported_providers()
