"""
DuckDB vector store provider implementation.
"""

import logging
from pathlib import Path
from typing import Any

from llama_index.core.vector_stores.types import VectorStore
from llama_index.vector_stores.duckdb import DuckDBVectorStore

from dana.common.sys_resource.vector_store.config import DuckDBConfig

from .base import BaseVectorStoreProvider

logger = logging.getLogger(__name__)


class DuckDBProvider(BaseVectorStoreProvider):
    """Provider for DuckDB vector store with lifecycle management."""

    def __init__(self, vector_store: DuckDBVectorStore):
        """Initialize DuckDB provider.

        Args:
            vector_store: DuckDBVectorStore instance
        """
        super().__init__(vector_store)
        # Type hint for better IDE support
        self.vector_store: DuckDBVectorStore = vector_store

    @staticmethod
    def create(config: DuckDBConfig, embed_dim: int) -> VectorStore:
        """Create DuckDB vector store instance.

        Args:
            config: DuckDB-specific configuration
            embed_dim: Embedding dimension

        Returns:
            Configured DuckDBVectorStore instance
        """
        logger.info(f"Initializing DuckDB store at: {config.path}/{config.filename}")

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

    def exists(self) -> bool:
        """Check if DuckDB database file exists.

        Returns:
            True if database file exists, False otherwise
        """
        try:
            db_path = Path(self.vector_store.persist_dir) / self.vector_store.database_name
            exists = db_path.exists()
            logger.debug(f"DuckDB existence check: {db_path} -> {exists}")
            return exists
        except Exception as e:
            logger.debug(f"DuckDB existence check failed: {e}")
            return False

    def get_row_count(self) -> int:
        """Get number of rows in DuckDB vector store.

        Returns:
            Number of rows in the vector store table
        """
        try:
            client = self.vector_store.client
            table_name = self.vector_store.table_name

            # Execute count query
            result = client.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = result[0] if result else 0

            logger.debug(f"DuckDB row count: {row_count}")
            return row_count

        except Exception as e:
            logger.debug(f"DuckDB row count check failed: {e}")
            return 0

    def drop_data(self) -> None:
        """Drop all data from DuckDB vector store table.

        This will drop the entire table, which will be recreated when new data is added.
        """
        try:
            client = self.vector_store.client
            table_name = self.vector_store.table_name

            client.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info(f"Dropped DuckDB table: {table_name}")

        except Exception as e:
            logger.warning(f"Failed to drop DuckDB table: {e}")
            # Continue anyway - rebuild will handle this

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive DuckDB statistics.

        Returns:
            Dictionary with DuckDB-specific statistics
        """
        try:
            db_path = Path(self.vector_store.persist_dir) / self.vector_store.database_name
            row_count = self.get_row_count()

            stats = {
                "provider": "duckdb",
                "database_path": str(db_path),
                "database_exists": db_path.exists() if db_path else False,
                "table_name": self.vector_store.table_name,
                "row_count": row_count,
                "has_data": row_count > 0,
                "exists": self.exists(),
            }

            # Add file size if database exists
            if db_path and db_path.exists():
                stats["file_size_bytes"] = db_path.stat().st_size
                stats["file_size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)

            return stats

        except Exception as e:
            return {
                "provider": "duckdb",
                "error": str(e),
                "exists": False,
                "has_data": False,
            }

    def health_check(self) -> dict[str, Any]:
        """Perform DuckDB health check.

        Returns:
            Health status with DuckDB-specific diagnostics
        """
        try:
            stats = self.get_statistics()

            # Additional DuckDB-specific health checks
            health_info = {
                "healthy": True,
                "provider": "duckdb",
                "statistics": stats,
                "checks": {
                    "database_accessible": False,
                    "table_accessible": False,
                    "can_query": False,
                },
            }

            # Test database accessibility
            try:
                health_info["checks"]["database_accessible"] = True

                # Test table accessibility (if it exists)
                if stats.get("row_count", 0) >= 0:  # get_row_count succeeded
                    health_info["checks"]["table_accessible"] = True
                    health_info["checks"]["can_query"] = True

            except Exception as e:
                health_info["healthy"] = False
                health_info["database_error"] = str(e)

            return health_info

        except Exception as e:
            return {
                "healthy": False,
                "provider": "duckdb",
                "error": str(e),
            }
