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


def create_default_llamaindex_embedding(config_override: dict[str, Any] | None = None):
    """Create a LlamaIndex embedding model using default config auto-selection.

    Automatically selects the first available model from 'preferred_models' in dana_config.json.

    Args:
        config_override: Optional configuration overrides

    Returns:
        LlamaIndex BaseEmbedding instance

    Raises:
        EmbeddingError: If no models are available or configuration is invalid

    Example:
        # Uses first available model from preferred_models in dana_config.json
        embed_model = create_default_llamaindex_embedding()
    """
    try:
        config = ConfigLoader().get_default_config()
        if config_override:
            config = {**config, **config_override}

        embedding_config = config.get("embedding", {})
        preferred_models = embedding_config.get("preferred_models", [])

        if not preferred_models:
            raise EmbeddingError("No preferred_models found in embedding configuration")

        # Try each preferred model until we find one that's available
        for model_name in preferred_models:
            if _is_model_available(model_name):
                return create_llamaindex_embedding(model_name, config_override)

        # If no models are available, provide helpful error message
        available_providers = []
        for model in preferred_models:
            if ":" in model:
                provider = model.split(":", 1)[0]
                if provider not in available_providers:
                    available_providers.append(provider)

        raise EmbeddingError(
            f"No available models found from preferred list: {preferred_models}. "
            f"Please check API keys for providers: {available_providers}"
        )

    except Exception as e:
        if isinstance(e, EmbeddingError):
            raise
        raise EmbeddingError(f"Failed to create default embedding model: {e}")


def _is_model_available(model_name: str) -> bool:
    """Check if a model is available by validating required API keys.

    Args:
        model_name: Model name in format "provider:model_name"

    Returns:
        True if model is available (API keys present), False otherwise
    """
    if ":" not in model_name:
        return False

    provider = model_name.split(":", 1)[0]

    # Check provider-specific requirements
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    elif provider == "huggingface":
        # HuggingFace models can work without API key for local models
        return True
    elif provider == "cohere":
        return bool(os.getenv("COHERE_API_KEY"))
    else:
        return False


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

    def get_default_embedding_model(self):
        """Get a LlamaIndex embedding model using auto-selection from config.

        Returns:
            LlamaIndex BaseEmbedding instance using first available preferred model
        """
        try:
            return create_default_llamaindex_embedding(self.config_override)
        except Exception as e:
            self.error(f"Failed to create default embedding model: {e}")
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

    def setup_default_globals(self, chunk_size: int = 2048):
        """Configure LlamaIndex global settings using auto-selected model.

        Args:
            chunk_size: Document chunk size
        """
        try:
            # Get the default model first to log which one was selected
            embed_model = create_default_llamaindex_embedding(self.config_override)

            from llama_index.core import Settings

            Settings.embed_model = embed_model
            Settings.chunk_size = chunk_size

            # Try to get model name for logging (if available)
            model_name = getattr(embed_model, "model_name", "auto-selected")
            self.info(f"Configured LlamaIndex with auto-selected model: {model_name}")
        except Exception as e:
            self.error(f"Failed to configure LlamaIndex with default model: {e}")
            raise


# Simple aliases for convenience
get_embedding_model = create_llamaindex_embedding
get_default_embedding_model = create_default_llamaindex_embedding
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
