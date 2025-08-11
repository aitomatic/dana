"""
Vector Store Resource Module for Dana.

This module provides a unified interface for vector store operations across
different providers (DuckDB, PostgreSQL/PGVector) with clean configuration
and factory patterns.

Key Features:
- Structured configuration with validation
- Provider-specific implementations
- Standardized factory interface with multiple creation methods
- Support for backward compatibility

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .config import (
    VectorStoreConfig,
    DuckDBConfig,
    PGVectorConfig,
    HNSWConfig,
    create_duckdb_config,
    create_pgvector_config,
)
from .factory import VectorStoreFactory
from .providers import DuckDBProvider, PGVectorProvider, VectorStoreProviderProtocol, BaseVectorStoreProvider

__all__ = [
    # Main configuration classes
    "VectorStoreConfig",
    "DuckDBConfig",
    "PGVectorConfig",
    "HNSWConfig",
    # Factory
    "VectorStoreFactory",
    # Provider interface
    "VectorStoreProviderProtocol",
    "BaseVectorStoreProvider",
    # Providers (for advanced use cases)
    "DuckDBProvider",
    "PGVectorProvider",
    # Helper functions
    "create_duckdb_config",
    "create_pgvector_config",
]
