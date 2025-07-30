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


class LlamaIndexEmbeddingResource(Loggable):
    """
    Manages LlamaIndex embedding models using Dana's configuration.

    This class provides a centralized way to create, configure, and manage
    LlamaIndex embedding models, ensuring that they are set up according
    to the global Dana configuration.
    """

    def __init__(self, config_override: dict[str, Any] | None = None):
        """Initialize resource.

        Args:
            config_override: Optional configuration overrides
        """
        super().__init__()
        self.config_override = config_override
        self._provider_factory = {
            "openai": self._create_openai_embedding,
            "cohere": self._create_cohere_embedding,
            "huggingface": self._create_huggingface_embedding,
        }

    def get_embedding_model(self, model_name: str):
        """Get a LlamaIndex embedding model.

        Args:
            model_name: Model to use (e.g., "openai:text-embedding-3-small")

        Returns:
            LlamaIndex BaseEmbedding instance
        """
        try:
            return self._create_llamaindex_embedding(model_name)
        except Exception as e:
            self.error(f"Failed to create embedding model: {e}")
            raise

    def get_default_embedding_model(self):
        """Get a LlamaIndex embedding model using auto-selection from config.

        Returns:
            LlamaIndex BaseEmbedding instance using first available preferred model
        """
        try:
            return self._create_default_llamaindex_embedding()
        except Exception as e:
            self.error(f"Failed to create default embedding model: {e}")
            raise

    def setup_global_settings(self, model_name: str, chunk_size: int = 2048):
        """Configure LlamaIndex global settings.

        Args:
            model_name: Model to use (e.g., "openai:text-embedding-3-small")
            chunk_size: Document chunk size
        """
        try:
            self._setup_llamaindex(model_name, chunk_size)
            self.info(f"Configured LlamaIndex with model: {model_name}")
        except Exception as e:
            self.error(f"Failed to configure LlamaIndex: {e}")
            raise

    def setup_default_global_settings(self, chunk_size: int = 2048):
        """Configure LlamaIndex global settings using auto-selected model.

        Args:
            chunk_size: Document chunk size
        """
        try:
            embed_model = self.get_default_embedding_model()
            from llama_index.core import Settings

            Settings.embed_model = embed_model
            Settings.chunk_size = chunk_size
            model_name = getattr(embed_model, "model_name", "auto-selected")
            self.info(f"Configured LlamaIndex with auto-selected model: {model_name}")
        except Exception as e:
            self.error(f"Failed to configure LlamaIndex with default model: {e}")
            raise

    def _get_config(self) -> dict[str, Any]:
        """Loads and returns the merged configuration."""
        config = ConfigLoader().get_default_config()
        if self.config_override:
            return self._deep_merge_dicts(config, self.config_override)
        return config

    def _create_llamaindex_embedding(self, model_name: str):
        """Create a LlamaIndex embedding model from Dana configuration."""
        if ":" not in model_name:
            raise EmbeddingError(f"Invalid model format: {model_name}. Expected 'provider:model_name'")

        provider, model_id = model_name.split(":", 1)

        if provider not in self._provider_factory:
            raise EmbeddingError(f"Unsupported provider: {provider}")

        try:
            config = self._get_config()
            provider_config = config.get("embedding", {}).get("provider_configs", {}).get(provider, {})

            creation_func = self._provider_factory[provider]
            return creation_func(model_id, provider_config)
        except Exception as e:
            raise EmbeddingError(f"Failed to create embedding for provider {provider}: {e}")

    def _create_default_llamaindex_embedding(self):
        """Create a LlamaIndex embedding model using default config auto-selection."""
        try:
            config = self._get_config()
            embedding_config = config.get("embedding", {})
            preferred_models = embedding_config.get("preferred_models", [])

            if not preferred_models:
                raise EmbeddingError("No preferred_models found in embedding configuration")

            for model_name in preferred_models:
                if self._is_model_available(model_name):
                    return self._create_llamaindex_embedding(model_name)

            available_providers = list(set(m.split(":", 1)[0] for m in preferred_models if ":" in m))
            raise EmbeddingError(
                f"No available models found from preferred list: {preferred_models}. "
                f"Please check API keys for providers: {available_providers}"
            )
        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Failed to create default embedding model: {e}")

    def _setup_llamaindex(self, model_name: str, chunk_size: int):
        """Setup LlamaIndex with Dana configuration."""
        try:
            from llama_index.core import Settings
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-core")

        embedding_model = self._create_llamaindex_embedding(model_name)
        Settings.embed_model = embedding_model
        Settings.chunk_size = chunk_size

    @staticmethod
    def _is_model_available(model_name: str) -> bool:
        """Check if a model is available by validating required API keys."""
        if ":" not in model_name:
            return False
        provider = model_name.split(":", 1)[0]
        if provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif provider == "huggingface":
            return True
        elif provider == "cohere":
            return bool(os.getenv("COHERE_API_KEY"))
        return False

    @staticmethod
    def _resolve_env_var(value: str) -> str:
        """Resolve environment variable if needed."""
        if isinstance(value, str) and value.startswith("env:"):
            return os.getenv(value[4:], "")
        return value

    def _create_openai_embedding(self, model_name: str, provider_config: dict[str, Any]):
        """Create OpenAI LlamaIndex embedding."""
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-openai")
        api_key = self._resolve_env_var(provider_config.get("api_key", ""))
        if not api_key:
            raise EmbeddingError("OpenAI API key not found")
        return OpenAIEmbedding(
            api_key=api_key,
            model=model_name,
            embed_batch_size=provider_config.get("batch_size", 100),
            dimensions=provider_config.get("dimension", 1024),
        )

    def _create_cohere_embedding(self, model_name: str, provider_config: dict[str, Any]):
        """Create Cohere LlamaIndex embedding."""
        try:
            from llama_index.embeddings.cohere import CohereEmbedding
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-cohere")
        api_key = self._resolve_env_var(provider_config.get("api_key", ""))
        if not api_key:
            raise EmbeddingError("Cohere API key not found")
        return CohereEmbedding(
            api_key=api_key,
            model_name=model_name,
            embed_batch_size=provider_config.get("batch_size", 100),
        )

    def _create_huggingface_embedding(self, model_name: str, provider_config: dict[str, Any]):
        """Create HuggingFace LlamaIndex embedding."""
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-huggingface")
        return HuggingFaceEmbedding(
            model_name=model_name,
            cache_folder=provider_config.get("cache_dir", ".cache/huggingface"),
        )

    def _deep_merge_dicts(self, base, override):
        """Deeply merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        return result


# For convenience and backward compatibility, create a default instance
_default_resource = LlamaIndexEmbeddingResource()
get_embedding_model = _default_resource.get_embedding_model
get_default_embedding_model = _default_resource.get_default_embedding_model
setup_llamaindex = _default_resource.setup_global_settings

# Alias for backward compatibility
RAGEmbeddingResource = LlamaIndexEmbeddingResource
