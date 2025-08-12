"""
Base protocol for vector store provider implementations.

This defines the standard interface that all vector store providers must implement
to support vector store lifecycle management and health checking.
"""

from typing import Protocol, Any
from llama_index.core.vector_stores.types import VectorStore


class VectorStoreProviderProtocol(Protocol):
    """Protocol defining the interface for vector store providers.

    Each vector store provider (DuckDB, PGVector, etc.) must implement these methods
    to support standardized vector store operations across the Dana platform.
    """

    def exists(self) -> bool:
        """Check if vector store exists and is accessible.

        Returns:
            True if vector store exists and is accessible, False otherwise
        """
        ...

    def has_data(self) -> bool:
        """Check if vector store contains embeddings/data.

        Returns:
            True if vector store has data, False otherwise
        """
        ...

    def get_row_count(self) -> int:
        """Get the number of rows/embeddings in the vector store.

        Returns:
            Number of rows in vector store, 0 if cannot determine
        """
        ...

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics about the vector store.

        Returns:
            Dictionary containing store statistics (row count, size, health, etc.)
        """
        ...

    def drop_data(self) -> None:
        """Drop/clear all data in the vector store.

        This method should safely remove all embeddings while preserving
        the store structure for rebuilding.
        """
        ...

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health and status check.

        Returns:
            Dictionary containing health status, connectivity, and diagnostic info
        """
        ...


class BaseVectorStoreProvider:
    """Base implementation for vector store providers.

    Provides common functionality and default implementations that can be
    shared across different vector store providers.
    """

    def __init__(self, vector_store: VectorStore):
        """Initialize provider with vector store instance.

        Args:
            vector_store: The vector store instance to wrap
        """
        self.vector_store = vector_store

    def has_data(self) -> bool:
        """Default implementation: check if row count > 0."""
        try:
            return self.get_row_count() > 0
        except Exception:
            return False

    def get_statistics(self) -> dict[str, Any]:
        """Default implementation: basic statistics."""
        try:
            row_count = self.get_row_count()
            return {
                "row_count": row_count,
                "exists": self.exists(),
                "has_data": row_count > 0,
                "provider": self.__class__.__name__,
            }
        except Exception as e:
            return {
                "error": str(e),
                "provider": self.__class__.__name__,
            }

    def health_check(self) -> dict[str, Any]:
        """Default implementation: combine existence and statistics."""
        try:
            stats = self.get_statistics()
            return {
                "healthy": stats.get("exists", False) and "error" not in stats,
                "statistics": stats,
                "provider": self.__class__.__name__,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "provider": self.__class__.__name__,
            }
