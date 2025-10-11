"""Configuration for Knowledge Organizations."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Settings for Redis connection."""

    url: str = "redis://localhost:6379"
    port: int = 6379
    db: int = 0
    password: str | None = None
    ssl: bool = False
    pool_size: int = 10
    timeout: int = 5

    model_config = SettingsConfigDict(env_prefix="KNOWS_REDIS_")


class PostgresSettings(BaseSettings):
    """Settings for PostgreSQL connection."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="knows")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    ssl: bool = Field(default=False)
    pool_size: int = Field(default=10)
    timeout: int = Field(default=5)  # seconds

    model_config = SettingsConfigDict(env_prefix="KNOWS_POSTGRES_")


class VectorStoreSettings(BaseSettings):
    """Settings for vector store."""

    host: str = "localhost"
    port: int = 5432
    database: str = "dana_test"
    user: str = "postgres"
    password: str = "postgres"
    ssl_mode: str = "disable"
    table: str = "vector_store"
    embedding_dim: int = 5

    model_config = ConfigDict(env_prefix="KNOWS_VECTOR_")


class TimeSeriesSettings(BaseSettings):
    """Settings for time series store."""

    host: str = "localhost"
    port: int = 5432
    database: str = "dana_test"
    user: str = "postgres"
    password: str = "postgres"
    ssl_mode: str = "disable"
    table: str = "time_series_store"
    default_interval: str = Field(default="1h")
    max_time_range: int = Field(default=30)  # days
    retention_period: int = Field(default=365)  # days

    model_config = ConfigDict(env_prefix="KNOWS_TIMESERIES_")


class RelationalSettings(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="knows")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    ssl_mode: str = Field(default="disable")


class KnowledgeSettings(BaseSettings):
    """Settings for knowledge organizations."""

    redis: RedisSettings = Field(default_factory=RedisSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    vector: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    time_series: TimeSeriesSettings = Field(default_factory=TimeSeriesSettings)

    model_config = ConfigDict(env_prefix="KNOWS_")
