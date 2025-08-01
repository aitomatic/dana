"""
Clean TabularIndexResource implementation using dependency injection.

Key improvements:
- Orchestrates component creation without config mutation
- Clean separation between configuration and component creation
- Easy to understand and maintain
- Proper error handling with clear messages
"""

from typing import Any
from collections.abc import Callable

from dana.common.resource.base_resource import BaseResource
from dana.common.resource.tabular_index.tabular_index import TabularIndex
from dana.common.resource.tabular_index.config import TabularConfig, EmbeddingConfig, BatchSearchConfig
from dana.common.resource.vector_store import VectorStoreFactory
from dana.common.resource.embedding import EmbeddingFactory
from dana.common.exceptions import EmbeddingError


class TabularIndexResource(BaseResource):
    """Clean tabular index resource using dependency injection.

    This class acts as an orchestrator that:
    1. Validates and creates configuration objects
    2. Uses factories to create components
    3. Injects dependencies into TabularIndex
    4. Provides a clean public API
    """

    def __init__(
        self,
        # Tabular data configuration
        source: str,
        embedding_field_constructor: Callable[[dict], str],
        table_name: str = "my_tabular_index",
        metadata_constructor: Callable[[dict], dict] | None = None,
        excluded_embed_metadata_keys: list[str] | None = None,
        cache_dir: str = ".cache/tabular_index",
        force_reload: bool = False,
        # Optional embedding override
        embedding_config: dict[str, Any] | None = None,
        # Optional vector store configuration
        vector_store_config: dict[str, Any] | None = None,
        # Resource metadata
        name: str = "tabular_index",
        description: str | None = None,
    ):
        """Initialize TabularIndexResource with clean configuration.

        Args:
            source: Path to data source (CSV or Parquet)
            embedding_field_constructor: Function to create embedding text from row
            table_name: Name for the index table
            metadata_constructor: Optional function to create metadata from row
            excluded_embed_metadata_keys: Keys to exclude from embedding metadata
            cache_dir: Directory for caching
            force_reload: Whether to force reload from source
            embedding_config: Optional embedding override in format:
                            {"model_name": "openai:text-embedding-3-large", "dimensions": 3072}
            vector_store_config: Optional vector store configuration
            name: Resource name
            description: Resource description
        """
        super().__init__(name, description)

        # Create clean configuration objects
        self._tabular_config = self._create_tabular_config(
            source=source,
            embedding_field_constructor=embedding_field_constructor,
            table_name=table_name,
            metadata_constructor=metadata_constructor,
            excluded_embed_metadata_keys=excluded_embed_metadata_keys or [],
            cache_dir=cache_dir,
            force_reload=force_reload,
        )

        self._embedding_config = self._create_embedding_config(embedding_config)
        self._vector_store_config = self._create_vector_store_config(vector_store_config)

        # Create components using factories (dependency injection)
        self._embedding_model, self._embed_dim = self._create_embedding_component()
        self._vector_store = self._create_vector_store_component()

        # Create TabularIndex with injected dependencies - clean and simple!
        self._tabular_index = TabularIndex(
            config=self._tabular_config, embedding_model=self._embedding_model, vector_store=self._vector_store
        )

        self._is_ready = False

    def _create_tabular_config(
        self,
        source: str,
        embedding_field_constructor: Callable[[dict], str],
        table_name: str,
        metadata_constructor: Callable[[dict], dict] | None,
        excluded_embed_metadata_keys: list[str],
        cache_dir: str,
        force_reload: bool,
    ) -> TabularConfig:
        """Create tabular configuration with validation.

        Returns:
            Validated TabularConfig object

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            return TabularConfig(
                source=source,
                embedding_field_constructor=embedding_field_constructor,
                table_name=table_name,
                metadata_constructor=metadata_constructor,
                excluded_embed_metadata_keys=excluded_embed_metadata_keys,
                cache_dir=cache_dir,
                force_reload=force_reload,
            )
        except Exception as e:
            raise ValueError(f"Invalid tabular configuration: {e}") from e

    def _create_embedding_config(self, embedding_config: dict[str, Any] | None) -> EmbeddingConfig | None:
        """Create embedding configuration from input.

        Args:
            embedding_config: Optional embedding configuration dict

        Returns:
            EmbeddingConfig object or None for defaults

        Raises:
            ValueError: If embedding configuration is invalid
        """
        if not embedding_config:
            return None

        try:
            return EmbeddingConfig(model_name=embedding_config["model_name"], dimensions=embedding_config.get("dimensions"))
        except KeyError as e:
            raise ValueError(f"Missing required embedding config field: {e}") from e
        except Exception as e:
            raise ValueError(f"Invalid embedding configuration: {e}") from e

    def _create_vector_store_config(self, vector_store_config: dict[str, Any] | None) -> dict[str, Any]:
        """Create vector store configuration dictionary for legacy compatibility.

        Args:
            vector_store_config: Optional vector store configuration

        Returns:
            Configuration dictionary in legacy format for VectorStoreFactory.create_from_legacy_dict
        """
        if not vector_store_config:
            # Provide sensible defaults in legacy format
            return {
                "provider": "duckdb",
                "storage_config": {"path": ".cache/vector_db", "filename": "tabular_index.db", "table_name": "vectors"},
            }

        # Return in legacy format
        return {"provider": vector_store_config.get("provider", "duckdb"), "storage_config": vector_store_config.get("storage_config", {})}

    def _create_embedding_component(self) -> tuple[Any, int]:
        """Create embedding component using factory.

        Returns:
            Tuple of (embedding_model, dimensions)

        Raises:
            EmbeddingError: If embedding creation fails
        """
        config_dict = {}
        try:
            if self._embedding_config:
                config_dict = {"model_name": self._embedding_config.model_name, "dimensions": self._embedding_config.dimensions}
            return EmbeddingFactory.create_from_dict(config_dict)
        except Exception as e:
            raise EmbeddingError(f"Failed to create embedding component: {e}") from e

    def _create_vector_store_component(self) -> Any:
        """Create vector store component using factory.

        Returns:
            Configured vector store

        Raises:
            ValueError: If vector store creation fails
        """
        try:
            # Use legacy dictionary format for backward compatibility
            return VectorStoreFactory.create_from_legacy_dict(self._vector_store_config, self._embed_dim)
        except Exception as e:
            raise ValueError(f"Failed to create vector store component: {e}") from e

    # Public API - delegates to TabularIndex

    async def initialize(self) -> None:
        """Initialize and preprocess sources."""
        await super().initialize()
        await self._tabular_index.initialize()
        self._is_ready = True

    async def retrieve(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Retrieve relevant documents."""
        if not self._is_ready:
            await self.initialize()

        return await self._tabular_index.retrieve(query, top_k)

    async def single_search(
        self, query: str, top_k: int = 10, callback: Callable[[str, list[dict[str, Any]]], None] | None = None
    ) -> dict[str, Any]:
        """Retrieve a single document."""
        if not self._is_ready:
            await self.initialize()

        return await self._tabular_index.single_search(query, top_k, callback)

    async def batch_search(
        self, queries: list[str], batch_search_config: dict[str, Any], callback: Callable[[str, list[dict[str, Any]]], None] | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve multiple documents."""
        if not self._is_ready:
            await self.initialize()

        # Convert dict to BatchSearchConfig
        batch_config = BatchSearchConfig(**batch_search_config)
        return await self._tabular_index.batch_search(queries, batch_config, callback)

    async def general_query(self, query: str, callback: Callable[[str, list[dict[str, Any]]], None] | None = None) -> list[dict[str, Any]]:
        """Retrieve multiple documents."""
        if not self._is_ready:
            await self.initialize()

        return await self._tabular_index.general_query(query, callback)

    # Configuration access (read-only)

    @property
    def tabular_config(self) -> TabularConfig:
        """Get tabular configuration (read-only)."""
        return self._tabular_config

    @property
    def embedding_config(self) -> EmbeddingConfig | None:
        """Get embedding configuration (read-only)."""
        return self._embedding_config

    @property
    def vector_store_config(self) -> dict[str, Any]:
        """Get vector store configuration (read-only)."""
        return self._vector_store_config
