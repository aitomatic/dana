"""
LLM Configuration Manager for Dana.

Simple model selection: check API keys, pick first available.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.exceptions import LLMError
from dana.common.utils.logging import DANA_LOGGER


class LLMConfigurationManager:
    """Simple LLM model selection and validation."""

    def __init__(self, explicit_model: str | None = None):
        """Initialize configuration manager.

        Args:
            explicit_model: Specific model to use, overrides auto-selection
        """
        self.explicit_model = explicit_model
        self.config_loader = ConfigLoader()
        self._selected_model = None

    @property
    def selected_model(self) -> str:
        """Get the currently selected model."""
        if self._selected_model is None:
            self._selected_model = self._determine_model()
        return self._selected_model

    @selected_model.setter
    def selected_model(self, value: str) -> None:
        """Set the model, with validation."""
        if not self._has_required_api_key(value):
            raise LLMError(f"Model '{value}' not available - missing API key")
        self._selected_model = value

    def _determine_model(self) -> str:
        """Determine which model to use."""
        # Mock mode
        if os.environ.get("DANA_MOCK_LLM", "").lower() == "true":
            return "mock:test-model"

        # Explicit model
        if self.explicit_model:
            if self._has_required_api_key(self.explicit_model):
                return self.explicit_model
            else:
                raise LLMError(f"Requested model '{self.explicit_model}' not available - missing API key")

        # Auto-selection
        auto_model = self._find_first_available_model()
        if auto_model:
            return auto_model

        raise LLMError("No available LLM models found. Please set API keys in your .env file.")

    def _find_first_available_model(self) -> str | None:
        """Find first model with API key set."""
        try:
            config = self.config_loader.get_default_config()
            preferred_models = config.get("llm", {}).get("preferred_models", [])

            if not preferred_models:
                DANA_LOGGER.warning("No preferred_models configured")
                return None

            DANA_LOGGER.debug(f"Checking preferred models: {preferred_models}")

            for model in preferred_models:
                # Handle both string and dict formats
                model_name = model if isinstance(model, str) else model.get("name") if isinstance(model, dict) else None

                if model_name and self._has_required_api_key(model_name):
                    DANA_LOGGER.info(f"✅ Selected model: {model_name}")
                    return model_name
                elif model_name:
                    DANA_LOGGER.debug(f"❌ Skipping model: {model_name} (no API key)")

            DANA_LOGGER.warning("No models have required API keys set")
            return None

        except Exception as e:
            DANA_LOGGER.error(f"Error finding first available model: {e}")
            return None

    def _has_required_api_key(self, model_name: str) -> bool:
        """Check if model has required API key."""
        if not model_name:
            return False

        # Mock models always available
        if model_name.startswith("mock:"):
            return True

        # Get provider and API key variable
        provider = self._get_provider_from_model(model_name)
        if not provider:
            return False

        api_key_var = self._get_api_key_var_for_provider(provider)
        if not api_key_var:
            return False

        # Check environment variable
        api_key_value = os.getenv(api_key_var)
        return bool(api_key_value and api_key_value.strip())

    def _get_provider_from_model(self, model_name: str) -> str | None:
        """Extract provider from model name."""
        if model_name == "local":
            return "local"
        elif ":" in model_name:
            return model_name.split(":", 1)[0]
        else:
            return None

    def _get_api_key_var_for_provider(self, provider: str) -> str | None:
        """Get API key environment variable name for provider."""
        api_key_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "cohere": "COHERE_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "local": "LOCAL_API_KEY",
            "ibm_watsonx": "WATSONX_API_KEY",
        }
        return api_key_vars.get(provider)

    def get_available_models(self) -> list[str]:
        """Get list of models with API keys set."""
        try:
            config = self.config_loader.get_default_config()
            preferred_models = config.get("llm", {}).get("preferred_models", [])
            available_models = []

            for model in preferred_models:
                # Handle both string and dict formats
                model_name = model if isinstance(model, str) else model.get("name") if isinstance(model, dict) else None

                if model_name and self._has_required_api_key(model_name):
                    available_models.append(model_name)

            return available_models

        except Exception as e:
            DANA_LOGGER.error(f"Error getting available models: {e}")
            return []

    def get_model_config(self, model: str | None = None) -> dict[str, Any]:
        """Get configuration for a specific model."""
        target_model = model or self.selected_model

        try:
            config = self.config_loader.get_default_config()
            model_configs = config.get("llm", {}).get("model_configs", {})

            # Get model-specific config or defaults
            return model_configs.get(target_model, {"max_tokens": 4096, "temperature": 0.7, "timeout": 30})

        except Exception:
            return {"max_tokens": 4096, "temperature": 0.7, "timeout": 30}
