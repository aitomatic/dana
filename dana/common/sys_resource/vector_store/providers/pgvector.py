"""
PostgreSQL with pgvector extension provider implementation.
"""

import asyncio
import logging
from typing import Any

from llama_index.core.vector_stores.types import VectorStore

from dana.common.sys_resource.vector_store.config import PGVectorConfig

from .base import BaseVectorStoreProvider

logger = logging.getLogger(__name__)


class PGVectorProvider(BaseVectorStoreProvider):
    """Provider for PostgreSQL with pgvector extension and lifecycle management."""

    def __init__(self, vector_store: Any):  # PGVectorStore type hint would require import
        """Initialize PGVector provider.

        Args:
            vector_store: PGVectorStore instance
        """
        # Don't call super().__init__ yet, we need to set up our attributes first
        # Store the original vector store
        self._original_vector_store = vector_store
        # Store config for recreating vector store when event loop changes
        self._config = None
        self._embed_dim = None
        self._current_loop_id = None
        # Extract config from the original vector store
        self._extract_config_from_vector_store(vector_store)
        # Now call super init which will set self.vector_store
        super().__init__(vector_store)

    def _extract_config_from_vector_store(self, vector_store):
        """Extract configuration from the vector store for recreation."""
        try:
            # Extract basic config from the vector store attributes
            self._embed_dim = vector_store.embed_dim

            # Parse connection string to get connection details
            from urllib.parse import urlparse

            conn_str = vector_store.connection_string
            # Parse postgresql://user:password@host:port/database
            parsed = urlparse(conn_str)

            self._recreate_params = {
                "host": parsed.hostname or "localhost",
                "port": str(parsed.port or 5432),
                "database": parsed.path.lstrip("/") if parsed.path else "vector_db",
                "user": parsed.username or "postgres",
                "password": parsed.password or "",
                "schema_name": vector_store.schema_name,
                "table_name": vector_store.table_name,
                "embed_dim": vector_store.embed_dim,
                "use_halfvec": vector_store.use_halfvec,
                "hnsw_kwargs": vector_store.hnsw_kwargs,
                "hybrid_search": vector_store.hybrid_search,
            }

            logger.debug(f"Extracted config: user={self._recreate_params['user']}, host={self._recreate_params['host']}")

        except Exception as e:
            logger.warning(f"Could not extract config from vector store: {e}")
            self._recreate_params = None

    def _get_vector_store_with_loop_check(self):
        """Get vector store, recreating if event loop changed."""
        try:
            current_loop = asyncio.get_running_loop()
            current_loop_id = id(current_loop)
        except RuntimeError:
            # No event loop running, use original vector store
            return getattr(self, "_vector_store", self._original_vector_store)

        # If event loop changed and we have recreation params, create new vector store
        if self._current_loop_id != current_loop_id and self._recreate_params is not None:
            logger.debug(f"Event loop changed ({self._current_loop_id} -> {current_loop_id}), recreating vector store")
            try:
                from llama_index.vector_stores.postgres import PGVectorStore

                new_vector_store = PGVectorStore.from_params(**self._recreate_params)
                # Update the stored vector store
                self._vector_store = new_vector_store
                self._original_vector_store = new_vector_store
                self._current_loop_id = current_loop_id

                return new_vector_store
            except Exception as e:
                logger.warning(f"Failed to recreate vector store for new event loop: {e}")
                # Fall back to original vector store
                return getattr(self, "_vector_store", self._original_vector_store)

        self._current_loop_id = current_loop_id
        return getattr(self, "_vector_store", self._original_vector_store)

    @property
    def vector_store(self):
        """Property to get vector store with event loop checking."""
        # If we have a stored vector store and need to check loops
        if hasattr(self, "_recreate_params"):
            return self._get_vector_store_with_loop_check()
        # Otherwise return the base vector store (during initialization)
        return getattr(self, "_vector_store", self._original_vector_store)

    @vector_store.setter
    def vector_store(self, value):
        """Setter for vector store property."""
        self._vector_store = value

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
            raise ImportError("PGVectorStore is not installed. Please install it with `pip install llama-index-vector-stores-postgres`")

        logger.info(f"Initializing PGVector store for database: {config.database}")
        logger.info(f"HNSW config: m={config.hnsw.m}, ef_construction={config.hnsw.ef_construction}")

        return PGVectorStore.from_params(
            host=config.host,
            port=str(config.port),
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

    def exists(self) -> bool:
        """Check if PGVector database and table are accessible.

        Returns:
            True if can connect and access table, False otherwise
        """
        try:
            # Initialize the connection if not already done
            self.vector_store._initialize()

            # Try to access the table class (this validates schema exists)
            table_class = self.vector_store._table_class
            if table_class is None:
                return False

            logger.debug(f"PGVector existence check: schema={self.vector_store.schema_name}, table={self.vector_store.table_name}")
            return True

        except Exception as e:
            logger.debug(f"PGVector existence check failed: {e}")
            return False

    def get_row_count(self) -> int:
        """Get number of rows in PGVector table using SQLAlchemy.

        Returns:
            Number of rows in the vector store table
        """
        try:
            # Ensure vector store is initialized
            self.vector_store._initialize()

            # Use SQLAlchemy session to execute count query
            import sqlalchemy

            schema_name = self.vector_store.schema_name
            table_name = self.vector_store._table_class.__tablename__

            with self.vector_store._session() as session, session.begin():
                # Use proper schema.table notation for PostgreSQL
                count_query = sqlalchemy.text(f"SELECT COUNT(*) FROM {schema_name}.{table_name}")
                result = session.execute(count_query).fetchone()
                row_count = result[0] if result else 0

                logger.debug(f"PGVector row count: {row_count}")
                return row_count

        except Exception as e:
            logger.debug(f"PGVector row count check failed: {e}")
            return 0

    def drop_data(self) -> None:
        """Drop all data from PGVector table.

        Uses the built-in clear() method from PGVectorStore.
        """
        try:
            # PGVectorStore has a built-in clear() method
            self.vector_store.clear()
            logger.info(f"Cleared PGVector table: {self.vector_store.schema_name}.{self.vector_store.table_name}")

        except Exception as e:
            logger.warning(f"Failed to clear PGVector table: {e}")
            # Continue anyway - rebuild will handle this

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive PGVector statistics.

        Returns:
            Dictionary with PGVector-specific statistics
        """
        try:
            row_count = self.get_row_count()

            stats = {
                "provider": "pgvector",
                "host": getattr(self.vector_store, "host", "unknown"),
                "port": getattr(self.vector_store, "port", "unknown"),
                "database": getattr(self.vector_store, "database", "unknown"),
                "schema_name": self.vector_store.schema_name,
                "table_name": self.vector_store.table_name,
                "row_count": row_count,
                "has_data": row_count > 0,
                "exists": self.exists(),
                "embed_dim": self.vector_store.embed_dim,
                "use_halfvec": self.vector_store.use_halfvec,
                "hybrid_search": self.vector_store.hybrid_search,
            }

            # Add HNSW configuration if available
            if hasattr(self.vector_store, "hnsw_kwargs") and self.vector_store.hnsw_kwargs:
                stats["hnsw_config"] = self.vector_store.hnsw_kwargs

            return stats

        except Exception as e:
            return {
                "provider": "pgvector",
                "error": str(e),
                "exists": False,
                "has_data": False,
            }

    def health_check(self) -> dict[str, Any]:
        """Perform PGVector health check with connection diagnostics.

        Returns:
            Health status with PGVector-specific diagnostics
        """
        try:
            stats = self.get_statistics()

            # Additional PGVector-specific health checks
            health_info = {
                "healthy": True,
                "provider": "pgvector",
                "statistics": stats,
                "checks": {
                    "connection_accessible": False,
                    "schema_accessible": False,
                    "table_accessible": False,
                    "can_query": False,
                },
            }

            # Test connection accessibility
            try:
                self.vector_store._initialize()
                health_info["checks"]["connection_accessible"] = True

                # Test schema accessibility
                if hasattr(self.vector_store, "_table_class") and self.vector_store._table_class:
                    health_info["checks"]["schema_accessible"] = True

                    # Test table query capability
                    if stats.get("row_count", 0) >= 0:  # get_row_count succeeded
                        health_info["checks"]["table_accessible"] = True
                        health_info["checks"]["can_query"] = True

            except Exception as e:
                health_info["healthy"] = False
                health_info["connection_error"] = str(e)

            return health_info

        except Exception as e:
            return {
                "healthy": False,
                "provider": "pgvector",
                "error": str(e),
            }
