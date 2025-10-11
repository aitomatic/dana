"""
Standardized factory for creating vector store instances.

This factory provides a clean, consistent interface for creating vector stores
across the entire codebase with proper provider abstraction.
"""

from llama_index.core.vector_stores.types import VectorStore

from .config import VectorStoreConfig, create_duckdb_config, create_pgvector_config
from .providers import DuckDBProvider, PGVectorProvider, VectorStoreProviderProtocol


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
    def create_with_provider(config: VectorStoreConfig, embed_dim: int) -> VectorStoreProviderProtocol:
        """Create vector store provider with lifecycle management.

        This method creates a provider wrapper that implements the VectorStoreProviderProtocol
        for lifecycle management operations. The vector store is accessible via provider.vector_store.

        Args:
            config: Structured vector store configuration
            embed_dim: Embedding dimension

        Returns:
            Provider wrapper (vector store accessible via provider.vector_store)

        Raises:
            ValueError: If unsupported provider or invalid configuration

        Example:
            config = create_duckdb_config(path=".cache/vectors")
            provider = VectorStoreFactory.create_with_provider(config, 1536)

            # Use vector store for LlamaIndex operations
            index = VectorStoreIndex([], storage_context=StorageContext.from_defaults(vector_store=provider.vector_store))

            # Use provider for lifecycle management
            if not provider.exists() or not provider.has_data():
                # Need to rebuild
                pass
        """
        if config.provider == "duckdb":
            provider_config = config.duckdb
            DuckDBProvider.validate_config(provider_config)
            vector_store = DuckDBProvider.create(provider_config, embed_dim)
            # Type cast is safe since DuckDBProvider.create returns DuckDBVectorStore
            provider = DuckDBProvider(vector_store)  # type: ignore
            return provider

        elif config.provider == "pgvector":
            provider_config = config.pgvector
            PGVectorProvider.validate_config(provider_config)
            vector_store = PGVectorProvider.create(provider_config, embed_dim)
            # Type cast is safe since PGVectorProvider.create returns PGVectorStore
            provider = PGVectorProvider(vector_store)  # type: ignore
            return provider

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
