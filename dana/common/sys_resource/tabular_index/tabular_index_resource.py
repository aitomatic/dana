"""
Clean TabularIndexResource implementation using dependency injection.

Key improvements:
- Orchestrates component creation without config mutation
- Clean separation between configuration and component creation
- Easy to understand and maintain
- Proper error handling with clear messages
"""

import threading
from collections.abc import Callable
from typing import Any

from dana.common.exceptions import EmbeddingError
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.embedding import EmbeddingFactory
from dana.common.sys_resource.tabular_index.config import BatchSearchConfig, EmbeddingConfig, TabularConfig
from dana.common.sys_resource.tabular_index.tabular_index import TabularIndex
from dana.common.sys_resource.vector_store import VectorStoreFactory


class TabularIndexResource(BaseSysResource):
    """Singleton tabular index resource using dependency injection."""

    _instance = None
    _lock = threading.Lock()
    _initialized = False  # Add this flag

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False  # Initialize flag
            return cls._instance

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
        """Initialize TabularIndexResource with clean configuration."""
        # Prevent re-initialization in singleton
        if getattr(self, "_initialized", False):
            return

        # Add double-check pattern for thread safety
        with self._lock:
            if getattr(self, "_initialized", False):
                return

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
            self._vector_store_provider = self._create_vector_store_component()

            # Create TabularIndex with injected dependencies - clean and simple!
            self._tabular_index = TabularIndex(
                config=self._tabular_config, embedding_model=self._embedding_model, provider=self._vector_store_provider
            )

            self._is_ready = False
            self._initialized = True  # Mark as initialized

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

    def _create_vector_store_config(self, vector_store_config: dict[str, Any] | None):
        """Create structured vector store configuration.

        Uses the user-provided cache_dir and table_name from TabularConfig instead of hardcoded values.
        This ensures proper resource isolation with separate DB files per resource.

        Args:
            vector_store_config: Optional vector store configuration

        Returns:
            Structured VectorStoreConfig object for VectorStoreFactory.create_with_provider
        """
        from dana.common.sys_resource.vector_store import create_duckdb_config, create_pgvector_config

        if not vector_store_config:
            # Use tabular config values to create structured config
            safe_table_name = self._sanitize_filename(self._tabular_config.table_name)
            return create_duckdb_config(
                path=self._tabular_config.cache_dir,  # Use user's cache_dir
                filename=f"{safe_table_name}.db",  # Use table_name for filename
                table_name=self._tabular_config.table_name,  # Use user's table_name
            )

        # Convert provided config to structured format
        provider_name = vector_store_config.get("provider", "duckdb")
        storage_config = vector_store_config.get("storage_config", {})

        if provider_name == "duckdb":
            return create_duckdb_config(
                path=storage_config.get("path", self._tabular_config.cache_dir),
                filename=storage_config.get("filename", f"{self._sanitize_filename(self._tabular_config.table_name)}.db"),
                table_name=storage_config.get("table_name", self._tabular_config.table_name),
            )
        elif provider_name == "pgvector":
            # Handle nested structure directly - much cleaner!
            return create_pgvector_config(
                host=storage_config.get("host", "localhost"),
                port=storage_config.get("port", 5432),
                database=storage_config.get("database", "vector_db"),
                user=storage_config.get("user", "postgres"),
                password=storage_config.get("password", ""),
                schema_name=storage_config.get("schema_name", "public"),
                table_name=storage_config.get("table_name", "vectors"),
                use_halfvec=storage_config.get("use_halfvec", False),
                hybrid_search=storage_config.get("hybrid_search", False),
                hnsw_config=storage_config.get("hnsw", None),  # Pass nested config directly
            )
        else:
            raise ValueError(f"Unsupported vector store provider: {provider_name}")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize table name for use as filename.

        Replaces problematic characters with underscores and truncates if too long.

        Args:
            name: Original table name

        Returns:
            Sanitized filename safe for filesystem use
        """
        import re

        # Replace problematic characters with underscores
        safe_name = re.sub(r"[^\w\-_.]", "_", name)
        # Truncate if too long (common filesystem limit is 255, leave room for .db extension)
        return safe_name[:200]

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
        """Create vector store provider using factory.

        Returns:
            Vector store provider (which contains the vector store)

        Raises:
            ValueError: If vector store creation fails
        """
        try:
            # Use structured config directly - much cleaner!
            return VectorStoreFactory.create_with_provider(self._vector_store_config, self._embed_dim)
        except Exception as e:
            raise ValueError(f"Failed to create vector store component: {e}") from e

    # Public API - delegates to TabularIndex
    def retrieve_all(self) -> list:
        """Retrieve all documents."""
        return [1, 2, 3]

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
    def vector_store_config(self):
        """Get vector store configuration (read-only)."""
        return self._vector_store_config
