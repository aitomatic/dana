"""
Clean configuration classes for TabularIndex system.

Follows separation of concerns principle:
- TabularConfig: Data source and processing configuration
- EmbeddingConfig: Embedding model configuration
- VectorStoreConfig: Vector storage configuration
"""

from dataclasses import dataclass, field
from collections.abc import Callable
from pathlib import Path


@dataclass
class TabularConfig:
    """Configuration for tabular data processing.

    Handles only data source and processing concerns.
    """

    source: str
    embedding_field_constructor: Callable[[dict], str]
    table_name: str = "my_tabular_index"
    metadata_constructor: Callable[[dict], dict] | None = None
    excluded_embed_metadata_keys: list[str] = field(default_factory=list)
    cache_dir: str = ".cache/tabular_index"
    force_reload: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.source:
            raise ValueError("Source file path cannot be empty")

        source_path = Path(self.source)
        valid_extensions = {".csv", ".parquet"}

        if source_path.suffix.lower() not in valid_extensions:
            raise ValueError(
                f"Source file must be a CSV or Parquet file. Got '{source_path.suffix}' but expected one of: {', '.join(valid_extensions)}"
            )


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model.

    Handles only embedding model concerns.
    """

    model_name: str
    dimensions: int | None = None  # Auto-detect if None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if ":" not in self.model_name:
            raise ValueError(f"Invalid model format: {self.model_name}. Expected 'provider:model_name'")


@dataclass
class BatchSearchConfig:
    """Configuration for batch search operations."""

    batch_size: int = 20
    pre_filter_top_k: int = 100
    post_filter_top_k: int = 20
    top_k: int = 10
