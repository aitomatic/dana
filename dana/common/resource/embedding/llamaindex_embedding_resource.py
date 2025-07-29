"""LlamaIndex Embedding Resource for Dana.

Simple integration between Dana's embedding configuration and LlamaIndex.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import EmbeddingError
from dana.common.mixins.loggable import Loggable


def create_llamaindex_embedding(model_name: str, config_override: dict[str, Any] | None = None):
    """Create a LlamaIndex embedding model from Dana configuration.

    Args:
        model_name: Model in format "provider:model_name" (e.g., "openai:text-embedding-3-small")
        config_override: Optional configuration overrides

    Returns:
        LlamaIndex BaseEmbedding instance

    Example:
        embed_model = create_llamaindex_embedding("openai:text-embedding-3-small")
    """
    if ":" not in model_name:
        raise EmbeddingError(f"Invalid model format: {model_name}. Expected 'provider:model_name'")

    provider, model_id = model_name.split(":", 1)

    # Load Dana configuration
    try:
        config = ConfigLoader().get_default_config()
        if config_override:
            config = {**config, **config_override}

        provider_config = config.get("embedding", {}).get("provider_configs", {}).get(provider, {})

    except Exception as e:
        raise EmbeddingError(f"Failed to load configuration: {e}")

    # Create model based on provider
    if provider == "openai":
        return _create_openai_embedding(model_id, provider_config)
    elif provider == "cohere":
        return _create_cohere_embedding(model_id, provider_config)
    elif provider == "huggingface":
        return _create_huggingface_embedding(model_id, provider_config)
    else:
        raise EmbeddingError(f"Unsupported provider: {provider}")


def setup_llamaindex(model_name: str, chunk_size: int = 2048):
    """Setup LlamaIndex with Dana configuration in one line.

    Args:
        model_name: Model to use (e.g., "openai:text-embedding-3-small")
        chunk_size: Document chunk size

    Example:
        setup_llamaindex("openai:text-embedding-3-small")
    """
    try:
        from llama_index.core import Settings
    except ImportError:
        raise EmbeddingError("Install: pip install llama-index-core")

    embedding_model = create_llamaindex_embedding(model_name)
    Settings.embed_model = embedding_model
    Settings.chunk_size = chunk_size


class LlamaIndexEmbeddingResource(Loggable):
    """Simple LlamaIndex embedding resource using Dana configuration."""

    def __init__(self, config_override: dict[str, Any] | None = None):
        """Initialize resource.

        Args:
            config_override: Optional configuration overrides
        """
        super().__init__()
        self.config_override = config_override

    def get_embedding_model(self, model_name: str):
        """Get a LlamaIndex embedding model.

        Args:
            model_name: Model to use (e.g., "openai:text-embedding-3-small")

        Returns:
            LlamaIndex BaseEmbedding instance
        """
        try:
            return create_llamaindex_embedding(model_name, self.config_override)
        except Exception as e:
            self.error(f"Failed to create embedding model: {e}")
            raise

    def setup_globals(self, model_name: str, chunk_size: int = 2048):
        """Configure LlamaIndex global settings.

        Args:
            model_name: Model to use (e.g., "openai:text-embedding-3-small")
            chunk_size: Document chunk size
        """
        try:
            setup_llamaindex(model_name, chunk_size)
            self.info(f"Configured LlamaIndex with model: {model_name}")
        except Exception as e:
            self.error(f"Failed to configure LlamaIndex: {e}")
            raise


# Simple aliases for convenience
get_embedding_model = create_llamaindex_embedding
RAGEmbeddingResource = LlamaIndexEmbeddingResource  # Backward compatibility


# Private helper functions
def _resolve_env_var(value: str) -> str:
    """Resolve environment variable if needed."""
    if isinstance(value, str) and value.startswith("env:"):
        env_var = value[4:]
        return os.getenv(env_var, "")
    return value


def _create_openai_embedding(model_name: str, provider_config: dict[str, Any]):
    """Create OpenAI LlamaIndex embedding."""
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
    except ImportError:
        raise EmbeddingError("Install: pip install llama-index-embeddings-openai")

    api_key = _resolve_env_var(provider_config.get("api_key", ""))
    if not api_key:
        raise EmbeddingError("OpenAI API key not found")

    return OpenAIEmbedding(
        api_key=api_key,
        model=model_name,
        embed_batch_size=provider_config.get("batch_size", 100),
        dimensions=provider_config.get("dimension", 1024),
    )


def _create_cohere_embedding(model_name: str, provider_config: dict[str, Any]):
    """Create Cohere LlamaIndex embedding."""
    try:
        from llama_index.embeddings.cohere import CohereEmbedding
    except ImportError:
        raise EmbeddingError("Install: pip install llama-index-embeddings-cohere")

    api_key = _resolve_env_var(provider_config.get("api_key", ""))
    if not api_key:
        raise EmbeddingError("Cohere API key not found")

    return CohereEmbedding(
        api_key=api_key,
        model_name=model_name,
        embed_batch_size=provider_config.get("batch_size", 100),
    )


def _create_huggingface_embedding(model_name: str, provider_config: dict[str, Any]):
    """Create HuggingFace LlamaIndex embedding."""
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError:
        raise EmbeddingError("Install: pip install llama-index-embeddings-huggingface")

    return HuggingFaceEmbedding(
        model_name=model_name,
        cache_folder=provider_config.get("cache_dir", ".cache/huggingface"),
    )
