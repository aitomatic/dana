"""LlamaIndex Embedding Resource for Dana.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import EmbeddingError
from dana.common.mixins.loggable import Loggable


class LlamaIndexEmbeddingResource(Loggable):
    """LlamaIndex embedding integration using Dana configuration."""

    def __init__(self, config_override: dict[str, Any] | None = None):
        """Initialize the LlamaIndex embedding resource."""
        super().__init__()
        self.config_override = config_override

    def get_embedding_model(self, model_name: str, dimension_override: int | None = None):
        """Get a LlamaIndex embedding model.

        Args:
            model_name: Model name in format 'provider:model_name'
            dimension_override: Override embedding dimension from upstream config
        """
        return self._create_embedding(model_name, dimension_override)

    def get_default_embedding_model(self, dimension_override: int | None = None):
        """Get a LlamaIndex embedding model using auto-selection."""
        config = self._get_config()
        preferred_models = config.get("embedding", {}).get("preferred_models", [])

        for model_name in preferred_models:
            if self._is_model_available(model_name):
                try:
                    return self._create_embedding(model_name, dimension_override)
                except Exception as e:
                    self.debug(f"Failed to create embedding model {model_name}: {e}")
                    continue

        raise EmbeddingError("No available embedding models found. Check API keys.")

    def setup_llamaindex(self, model_name: str | None = None, chunk_size: int = 2048):
        """Configure LlamaIndex global settings."""
        try:
            from llama_index.core import Settings
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-core")

        if model_name:
            embed_model = self.get_embedding_model(model_name)
        else:
            embed_model = self.get_default_embedding_model()

        Settings.embed_model = embed_model
        Settings.chunk_size = chunk_size

    def _get_config(self) -> dict[str, Any]:
        """Load configuration from Dana config."""
        config = ConfigLoader().get_default_config()
        if self.config_override:
            # Deep merge for nested dictionaries
            return self._merge_configs(config, self.config_override)
        return config

    def _merge_configs(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Merge configurations with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _create_embedding(self, model_name: str, dimension_override: int | None = None):
        """Create a LlamaIndex embedding model.

        Args:
            model_name: Model name in format 'provider:model_name'
            dimension_override: Override embedding dimension from upstream config
        """
        if ":" not in model_name:
            raise EmbeddingError(f"Invalid model format: {model_name}. Expected 'provider:model_name'")

        provider, model_id = model_name.split(":", 1)
        config = self._get_config()
        provider_config = config.get("embedding", {}).get("provider_configs", {}).get(provider, {})

        if provider == "openai":
            return self._create_openai_embedding(model_id, provider_config, dimension_override)
        if provider == "azure":
            return self._create_azure_embedding(model_id, provider_config, dimension_override)
        elif provider == "cohere":
            return self._create_cohere_embedding(model_id, provider_config, dimension_override)
        elif provider == "huggingface":
            return self._create_huggingface_embedding(model_id, provider_config, dimension_override)
        else:
            raise EmbeddingError(f"Unsupported provider: {provider}")

    @staticmethod
    def _is_model_available(model_name: str) -> bool:
        """Check if a model is available by validating API keys."""
        if ":" not in model_name:
            return False

        provider = model_name.split(":", 1)[0]
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "cohere": "COHERE_API_KEY",
            "huggingface": None,  # No API key required
        }

        required_key = key_mapping.get(provider)
        return required_key is None or bool(os.getenv(required_key))

    @staticmethod
    def _resolve_env_var(value: str, default: str = "") -> str:
        """Resolve environment variable if needed."""
        if isinstance(value, str) and value.startswith("env:"):
            return os.getenv(value[4:], default)
        return value

    def _create_openai_embedding(self, model_name: str, provider_config: dict[str, Any], dimension_override: int | None = None):
        """Create OpenAI LlamaIndex embedding.

        Args:
            model_name: OpenAI model name
            provider_config: Provider configuration from dana_config.json
            dimension_override: Override dimension from upstream config (takes precedence)
        """
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding  # type: ignore
            from llama_index.embeddings.openai.base import DEFAULT_OPENAI_API_BASE  # type: ignore
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-openai")

        api_key = self._resolve_env_var(provider_config.get("api_key", ""))
        base_url = self._resolve_env_var(provider_config.get("base_url", DEFAULT_OPENAI_API_BASE))

        if not api_key:
            raise EmbeddingError("OpenAI API key not found")

        # Use dimension_override if provided, else fall back to provider_config
        dimensions = dimension_override if dimension_override is not None else provider_config.get("dimension", 1024)

        try:
            embedding = OpenAIEmbedding(
                api_key=api_key,
                api_base=base_url,
                model=model_name,
                embed_batch_size=provider_config.get("batch_size", 100),
                dimensions=dimensions,
            )
            return embedding
        except Exception as _:
            # Retry embedding with `model_name` and don't use batch_size and dimensions
            embedding = OpenAIEmbedding(
                api_key=api_key,
                api_base=base_url,
                model_name=model_name,
            )
            embedding.get_text_embedding("test") # Try running embedding to see if it works
            print(f"\033[92mSuccessfully initialized embedding with model_name: {model_name}\033[0m")
            return embedding



    def _create_azure_embedding(self, model_name: str, provider_config: dict[str, Any], dimension_override: int | None = None):
        try:
            from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding  # type: ignore
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-azure")

        api_key = self._resolve_env_var(provider_config.get("api_key", ""))
        azure_endpoint = self._resolve_env_var(provider_config.get("base_url", ""))
        api_version = self._resolve_env_var(provider_config.get("api_version", ""), "2025-01-01-preview")
        if not api_key or not azure_endpoint:
            raise EmbeddingError("Azure embedding failed to initialize. Please provide both AZURE_OPENAI_API_KEY and AZURE_OPENAI_API_URL")
        
        # Use dimension_override if provided, else fall back to provider_config
        dimensions = dimension_override if dimension_override is not None else provider_config.get("dimension", 1024)

        return AzureOpenAIEmbedding(
            model=model_name,
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            embed_batch_size=provider_config.get("batch_size", 100),
            dimensions=dimensions,
        )

    def _create_cohere_embedding(self, model_name: str, provider_config: dict[str, Any], dimension_override: int | None = None):
        """Create Cohere LlamaIndex embedding.

        Args:
            model_name: Cohere model name
            provider_config: Provider configuration from dana_config.json
            dimension_override: Override dimension from upstream config (Note: Cohere models have fixed dimensions)
        """
        try:
            from llama_index.embeddings.cohere import CohereEmbedding  # type: ignore
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-cohere")

        api_key = self._resolve_env_var(provider_config.get("api_key", ""))
        if not api_key:
            raise EmbeddingError("Cohere API key not found")

        # Note: CohereEmbedding doesn't accept dimensions parameter - dimensions are model-specific
        # dimension_override is accepted for API consistency but not used
        return CohereEmbedding(
            api_key=api_key,
            model_name=model_name,
            embed_batch_size=provider_config.get("batch_size", 64),
        )

    def _create_huggingface_embedding(self, model_name: str, provider_config: dict[str, Any], dimension_override: int | None = None):
        """Create HuggingFace LlamaIndex embedding.

        Args:
            model_name: HuggingFace model name
            provider_config: Provider configuration from dana_config.json
            dimension_override: Override dimension from upstream config (Note: HF models have fixed dimensions)
        """
        try:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # type: ignore
        except ImportError:
            raise EmbeddingError("Install: pip install llama-index-embeddings-huggingface")

        # Note: HuggingFaceEmbedding doesn't accept dimensions parameter - dimensions are model-specific
        # dimension_override is accepted for API consistency but not used
        return HuggingFaceEmbedding(
            model_name=model_name,
            cache_folder=provider_config.get("cache_dir", ".cache/huggingface"),
            embed_batch_size=provider_config.get("batch_size", 10),
        )


class EmbeddingFactory:
    """Factory for creating embedding models with proper dimension handling.

    This factory provides a clean interface for creating embedding models
    across the entire codebase, not limited to any specific module.
    """

    @staticmethod
    def create_from_config(model_name: str | None = None, dimensions: int | None = None) -> tuple[Any, int]:
        """Create embedding model from simple configuration parameters.

        Args:
            model_name: Model name in format 'provider:model_name' or None for default
            dimensions: Explicit dimensions or None for auto-detection

        Returns:
            Tuple of (embedding_model, actual_dimensions)

        Raises:
            EmbeddingError: If embedding model creation fails
        """
        try:
            embedding_resource = LlamaIndexEmbeddingResource()

            if model_name:
                # Use specified model
                embedding_model = embedding_resource.get_embedding_model(model_name, dimensions)
            else:
                # Use default from dana_config.json
                embedding_model = embedding_resource.get_default_embedding_model(dimensions)
                
            actual_dimensions = dimensions if dimensions else EmbeddingFactory._extract_dimensions(embedding_model)

            return embedding_model, actual_dimensions

        except Exception as e:
            raise EmbeddingError(f"Failed to create embedding model: {e}") from e

    @staticmethod
    def create_from_dict(config: dict[str, Any] | None = None) -> tuple[Any, int]:
        """Create embedding model from dictionary configuration.

        Args:
            config: Configuration dict with 'model_name' and optional 'dimensions'
                   or None for defaults

        Returns:
            Tuple of (embedding_model, actual_dimensions)

        Raises:
            EmbeddingError: If embedding model creation fails
        """
        if not config:
            return EmbeddingFactory.create_from_config()

        model_name = config.get("model_name")
        dimensions = config.get("dimensions")

        return EmbeddingFactory.create_from_config(model_name, dimensions)

    @staticmethod
    def _extract_dimensions(embedding_model: Any) -> int:
        """Extract dimensions from embedding model.

        Args:
            embedding_model: LlamaIndex BaseEmbedding instance

        Returns:
            Embedding dimension

        Raises:
            EmbeddingError: If dimension cannot be determined
        """
        # Strategy 1: Try to get from model object attributes
        if hasattr(embedding_model, "dimensions") and embedding_model.dimensions:
            return embedding_model.dimensions

        # Strategy 2: Generate a test embedding to get dimension
        try:
            test_embedding = embedding_model.get_text_embedding("test")
            return len(test_embedding)
        except Exception as e:
            raise EmbeddingError(f"Cannot determine embedding dimension: {e}")


# Convenience functions using default instance
RAGEmbeddingResource = LlamaIndexEmbeddingResource
get_embedding_model = RAGEmbeddingResource().get_embedding_model
get_default_embedding_model = RAGEmbeddingResource().get_default_embedding_model
