"""Configuration settings for context management."""

from pydantic import Field
from pydantic_settings import BaseSettings


class ContextSettings(BaseSettings):
    """Settings for context management."""
    
    # Context persistence
    persistence_enabled: bool = Field(
        default=True,
        description="Enable context persistence to storage"
    )
    persistence_ttl: int = Field(
        default=3600,
        description="Time-to-live for persisted contexts in seconds"
    )
    
    # Context synchronization
    sync_interval: int = Field(
        default=60,
        description="Interval between context synchronizations in seconds"
    )
    max_sync_retries: int = Field(
        default=3,
        description="Maximum number of sync retry attempts"
    )
    sync_timeout: int = Field(
        default=30,
        description="Timeout for sync operations in seconds"
    )
    
    # Performance settings
    cache_size: int = Field(
        default=1000,
        description="Maximum number of contexts to cache in memory"
    )
    cache_ttl: int = Field(
        default=300,
        description="Time-to-live for cached contexts in seconds"
    )
    
    # Validation settings
    max_key_length: int = Field(
        default=256,
        description="Maximum length for context keys"
    )
    max_value_size: int = Field(
        default=1024 * 1024,  # 1MB
        description="Maximum size for context values in bytes"
    )
    max_context_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum total size for a context in bytes"
    )
    
    # Monitoring settings
    enable_metrics: bool = Field(
        default=True,
        description="Enable context metrics collection"
    )
    metrics_interval: int = Field(
        default=60,
        description="Interval for metrics collection in seconds"
    )
    
    model_config = {
        "env_prefix": "KNOWS_CONTEXT_",
        "case_sensitive": False
    } 