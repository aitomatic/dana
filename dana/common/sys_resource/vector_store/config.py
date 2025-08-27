"""
Configuration classes for vector store system.

Provides structured configuration for different vector store providers
with proper validation and defaults.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HNSWConfig:
    """Configuration for HNSW index parameters (used by PGVector)."""

    m: int = 64  # Number of bi-directional links for every new element
    ef_construction: int = 400  # Size of the dynamic candidate list
    ef_search: int = 400  # Size of the dynamic candidate list during search
    dist_method: str = "vector_cosine_ops"  # Distance method for HNSW index

    def to_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs format expected by PGVector."""
        return {
            "hnsw_m": self.m,
            "hnsw_ef_construction": self.ef_construction,
            "hnsw_ef_search": self.ef_search,
            "hnsw_dist_method": self.dist_method,
        }


@dataclass
class DuckDBConfig:
    """Configuration for DuckDB vector store."""

    path: str = ".cache/vector_db"  # Directory for DuckDB files
    filename: str = "vector_store.db"  # Database filename
    table_name: str = "vectors"  # Table name for vectors

    def __post_init__(self):
        """Validate configuration."""
        if not self.path:
            raise ValueError("DuckDB path cannot be empty")
        if not self.filename:
            raise ValueError("DuckDB filename cannot be empty")
        if not self.table_name:
            raise ValueError("DuckDB table_name cannot be empty")


@dataclass
class PGVectorConfig:
    """Configuration for PostgreSQL with pgvector extension."""

    host: str = "localhost"  # PostgreSQL host
    port: int = 5432  # PostgreSQL port
    database: str = "vector_db"  # Database name
    user: str = "postgres"  # Database user
    password: str = ""  # Database password
    schema_name: str = "public"  # Schema name
    table_name: str = "vectors"  # Table name for vectors
    use_halfvec: bool = False  # Use halfvec for storage efficiency
    hybrid_search: bool = False  # Enable hybrid search
    hnsw: HNSWConfig = field(default_factory=HNSWConfig)  # HNSW configuration

    def __post_init__(self):
        """Validate configuration."""
        if not self.host:
            raise ValueError("PostgreSQL host cannot be empty")
        if not isinstance(self.port, int) or self.port <= 0:
            raise ValueError("PostgreSQL port must be a positive integer")
        if not self.database:
            raise ValueError("PostgreSQL database cannot be empty")
        if not self.user:
            raise ValueError("PostgreSQL user cannot be empty")


@dataclass
class VectorStoreConfig:
    """Main configuration for vector store system.

    This is the primary configuration class that determines which vector store
    provider to use and contains provider-specific configurations.
    """

    provider: str  # Vector store provider ("duckdb" or "pgvector")
    duckdb: DuckDBConfig = field(default_factory=DuckDBConfig)
    pgvector: PGVectorConfig = field(default_factory=PGVectorConfig)

    def __post_init__(self):
        """Validate configuration."""
        supported_providers = ["duckdb", "pgvector"]
        if self.provider not in supported_providers:
            raise ValueError(f"Unsupported vector store provider: {self.provider}. Supported providers: {', '.join(supported_providers)}")

    def get_provider_config(self) -> DuckDBConfig | PGVectorConfig:
        """Get the configuration for the selected provider."""
        if self.provider == "duckdb":
            return self.duckdb
        elif self.provider == "pgvector":
            return self.pgvector
        else:
            raise ValueError(f"Unknown provider: {self.provider}")


# Backward compatibility - simple config creation helpers
def create_duckdb_config(
    path: str = ".cache/vector_db", filename: str = "vector_store.db", table_name: str = "vectors"
) -> VectorStoreConfig:
    """Create a DuckDB vector store configuration."""
    return VectorStoreConfig(provider="duckdb", duckdb=DuckDBConfig(path=path, filename=filename, table_name=table_name))


def create_pgvector_config(
    host: str = "localhost",
    port: int = 5432,
    database: str = "vector_db",
    user: str = "postgres",
    password: str = "",
    schema_name: str = "public",
    table_name: str = "vectors",
    use_halfvec: bool = False,
    hybrid_search: bool = False,
    hnsw_config: dict[str, Any] | None = None,
) -> VectorStoreConfig:
    """Create a PostgreSQL/PGVector configuration.

    Args:
        host: PostgreSQL host
        port: PostgreSQL port
        database: Database name
        user: PostgreSQL user
        password: PostgreSQL password
        schema_name: Schema name
        table_name: Table name for vectors
        use_halfvec: Whether to use half-precision vectors
        hybrid_search: Whether to enable hybrid search
        hnsw_config: HNSW configuration dict (e.g., {"m": 32, "ef_construction": 200})

    Returns:
        Structured VectorStoreConfig for PGVector
    """
    # Create HNSW config directly from nested dict - much cleaner!
    hnsw = HNSWConfig(**(hnsw_config or {}))

    return VectorStoreConfig(
        provider="pgvector",
        pgvector=PGVectorConfig(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            schema_name=schema_name,
            table_name=table_name,
            use_halfvec=use_halfvec,
            hybrid_search=hybrid_search,
            hnsw=hnsw,
        ),
    )
