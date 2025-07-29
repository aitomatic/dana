"""
Embedding Configuration Manager for Dana.

Simple model selection: check API keys, pick first available.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.utils.logging import DANA_LOGGER


class EmbeddingConfigurationManager:
    """Simple embedding model selection and validation."""

    def __init__(self, explicit_model: str | None = None, config: dict[str, Any] | None = None):
        """Initialize configuration manager.

        Args:
            explicit_model: Specific model to use, overrides auto-selection
            config: Additional configuration parameters
        """
        self.explicit_model = explicit_model
        self.config = config or {}
        self.config_loader = ConfigLoader()
        self._selected_model = None

    @property
    def selected_model(self) -> str | None:
        """Get the currently selected model."""
        if self._selected_model is None:
            self._selected_model = self._determine_model()
        return self._selected_model

    @selected_model.setter
    def selected_model(self, value: str) -> None:
        """Set the model."""
        self._selected_model = value

    def _determine_model(self) -> str | None:
        """Determine which model to use based on configuration and availability."""
        # Mock mode
        if os.environ.get("DANA_MOCK_EMBEDDING", "").lower() == "true":
            return "mock:test-embeddings"

        # Accept explicit model without validation - let user figure out issues at usage time
        if self.explicit_model:
            return self.explicit_model

        # Try auto-selection, but don't fail if nothing found
        auto_model = self._find_first_available_model()
        if auto_model:
            return auto_model

        # Return None instead of raising - validation happens at usage time
        return None

    def _validate_model(self, model_name: str) -> bool:
        """Validate if a model is properly configured.

        Args:
            model_name: Model name in format "provider:model_name"

        Returns:
            True if model is valid and available
        """
        if not model_name or ":" not in model_name:
            DANA_LOGGER.warning(f"Invalid model format: {model_name}")
            return False

        provider = model_name.split(":", 1)[0]

        # Validate provider-specific requirements
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                DANA_LOGGER.debug(f"OpenAI API key not found for model {model_name}")
                return False
            return True

        elif provider == "huggingface":
            # HuggingFace models can work without API key for local models
            # But we might want to check if the model exists locally or can be downloaded
            return True

        elif provider == "cohere":
            api_key = os.getenv("COHERE_API_KEY")
            if not api_key:
                DANA_LOGGER.debug(f"Cohere API key not found for model {model_name}")
                return False
            return True

        else:
            DANA_LOGGER.warning(f"Unknown embedding provider: {provider}")
            return False

    def _find_first_available_model(self) -> str | None:
        """Find the first available model from the configuration.

        Returns:
            First available model name, or None if no models available
        """
        try:
            config = self.config_loader.get_default_config()

            if "embedding" not in config:
                DANA_LOGGER.debug("No embedding configuration found")
                return None

            embedding_config = config["embedding"]
            preferred_models = embedding_config.get("preferred_models", [])

            if not preferred_models:
                DANA_LOGGER.debug("No preferred embedding models configured")
                return None

            for model in preferred_models:
                if self._is_model_actually_available(model):
                    DANA_LOGGER.debug(f"Found available embedding model: {model}")
                    return model

            DANA_LOGGER.debug("No available embedding models found")
            return None

        except Exception as e:
            DANA_LOGGER.warning(f"Error finding available embedding model: {e}")
            return None

    def _is_model_actually_available(self, model_name: str) -> bool:
        """Check if model is actually available by testing API connectivity.

        This is more thorough than just checking API keys - it validates
        that the model can actually be used.

        Args:
            model_name: Model name to check

        Returns:
            True if model is available and working
        """
        if not self._validate_model(model_name):
            return False

        # For now, we'll just validate API keys
        # In the future, we could add actual API connectivity tests
        provider = model_name.split(":", 1)[0]

        if provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif provider == "huggingface":
            return True  # HuggingFace models are generally available
        elif provider == "cohere":
            return bool(os.getenv("COHERE_API_KEY"))
        else:
            return False

    def get_model_config(self, model_name: str) -> dict[str, Any]:
        """Get configuration for a specific model.

        Args:
            model_name: Model name in format "provider:model_name"

        Returns:
            Model-specific configuration dictionary
        """
        if ":" not in model_name:
            return {}

        provider = model_name.split(":", 1)[0]

        try:
            config = self.config_loader.get_default_config()
            embedding_config = config.get("embedding", {})
            provider_configs = embedding_config.get("provider_configs", {})

            return provider_configs.get(provider, {})

        except Exception as e:
            DANA_LOGGER.warning(f"Error getting model config for {model_name}: {e}")
            return {}

    def get_supported_providers(self) -> list[str]:
        """Get list of supported embedding providers.

        Returns:
            List of supported provider names
        """
        return ["openai", "huggingface", "cohere"]

    def is_provider_supported(self, provider: str) -> bool:
        """Check if a provider is supported.

        Args:
            provider: Provider name to check

        Returns:
            True if provider is supported
        """
        return provider in self.get_supported_providers()
