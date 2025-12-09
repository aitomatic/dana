from collections.abc import AsyncGenerator

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .log_config import LOGGER_CONFIG


class Settings(BaseSettings):
    """Application settings."""

    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # App settings
    app_name: str = Field(default="star-agent-builder-api", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database configuration
    database_url: str = Field(default="sqlite+aiosqlite:///./star_agents.db", alias="DATABASE_URL")

    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND")

    # JWT authentication settings
    jwt_secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_issuer: str | None = Field(default=None, alias="JWT_ISSUER")
    jwt_audience: str | None = Field(default=None, alias="JWT_AUDIENCE")

    # LLM provider settings
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", alias="ANTHROPIC_MODEL")
    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_max_context_tokens: int = Field(default=4000, alias="DEFAULT_MAX_CONTEXT_TOKENS")


settings = Settings()

# Async SQLAlchemy setup with connection pooling
engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Number of connections to keep in pool
    max_overflow=10,  # Max connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        Async database session
    """
    async with SessionLocal() as session:
        yield session


__all__ = ["settings", "LOGGER_CONFIG", "engine", "SessionLocal", "get_session"]
