"""
Vector store provider implementations.

This module contains provider-specific implementations for different
vector store backends with standardized lifecycle management.
"""

from .base import VectorStoreProviderProtocol, BaseVectorStoreProvider
from .duckdb import DuckDBProvider
from .pgvector import PGVectorProvider

__all__ = [
    "VectorStoreProviderProtocol",
    "BaseVectorStoreProvider",
    "DuckDBProvider",
    "PGVectorProvider",
]
