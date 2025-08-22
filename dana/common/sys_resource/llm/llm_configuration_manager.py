"""
LLM Configuration Manager for Dana.

Simple model selection: check API keys, pick first available.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from dana.common.config.config_loader import ConfigLoader
from dana.common.utils.logging import DANA_LOGGER


class LLMConfigurationManager:
    """Simple LLM model selection and validation."""

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
        if os.environ.get("DANA_MOCK_LLM", "").lower() == "true":
            return "mock:test-model"

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
        """Validate if model is available (has required API key and is properly configured).

        For properly formatted models with known providers: validates API keys immediately.
        For improperly formatted models: allows setting (will fail at query time).

        Args:
            model_name: Name of the model to validate

        Returns:
            True if the model is available/settable, False only for known providers missing API keys
        """
        if not model_name:
            return False

        # Mock models always available
        if model_name.startswith("mock:"):
            return True

        try:
            # Get provider from model name
            provider = self._get_provider_from_model(model_name)
            if not provider:
                # If we can't extract a provider (invalid format), allow setting
                # This will fail at query time, which matches existing test expectations
                return True

            # Get configuration to check if provider is in provider_configs
            config = self.config_loader.get_default_config()
            provider_configs = config.get("llm", {}).get("provider_configs", {})

            # Check if this is a known provider type (has API key mapping)
            api_key_var = self._get_api_key_var_for_provider(provider)

            if provider not in provider_configs:
                # Provider not in config
                if api_key_var:
                    # This is a known provider type but not in config - validate API key
                    api_key_value = os.getenv(api_key_var)
                    return bool(api_key_value and api_key_value.strip())
                else:
                    # Unknown provider type with proper format - reject
                    # (This covers cases like "unknown:model" where "unknown" is not a known provider)
                    return False

            # Provider is in config - validate according to config requirements
            # Check if required API key is set for known providers
            if api_key_var:
                api_key_value = os.getenv(api_key_var)
                return bool(api_key_value and api_key_value.strip())

            # For providers without a predefined API key mapping,
            # check if there are any environment variable requirements in the provider config
            provider_config = provider_configs[provider]
            required_vars = []
            for _key, value in provider_config.items():
                if isinstance(value, str) and value.startswith("env:"):
                    env_var = value[4:]  # Remove "env:" prefix
                    required_vars.append(env_var)

            # Check if all required environment variables are set
            for env_var in required_vars:
                if not os.getenv(env_var):
                    return False

            return True

        except Exception:
            # On any exception, allow setting (will fail at query time if invalid)
            return True

    def _find_first_available_model(self) -> str | None:
        """Find first model with API key set."""
        try:
            config = self.config_loader.get_default_config()
            preferred_models = config.get("llm", {}).get("preferred_models", [])

            if not preferred_models:
                return None

            for model in preferred_models:
                # Handle both string and dict formats
                model_name = model if isinstance(model, str) else model.get("name") if isinstance(model, dict) else None

                if model_name and self._is_model_actually_available(model_name):
                    return model_name

            return None

        except Exception:
            return None

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

    def _is_model_actually_available(self, model_name: str) -> bool:
        """Strict validation for whether a model is actually available and usable.

        Used by get_available_models() - requires proper configuration and API keys.
        More strict than _validate_model() which allows setting invalid formats.
        """
        if not model_name:
            return False

        # Mock models always available
        if model_name.startswith("mock:"):
            return True

        try:
            # Get provider from model name
            provider = self._get_provider_from_model(model_name)
            if not provider:
                # Invalid format models are not considered "available"
                return False

            # Get configuration to check if provider is in provider_configs
            config = self.config_loader.get_default_config()
            provider_configs = config.get("llm", {}).get("provider_configs", {})

            # For availability, provider must be in config
            if provider not in provider_configs:
                # For known providers, check API key even if not in config
                api_key_var = self._get_api_key_var_for_provider(provider)
                if api_key_var:
                    api_key_value = os.getenv(api_key_var)
                    return bool(api_key_value and api_key_value.strip())
                else:
                    # Unknown provider not in config = not available
                    return False

            # Provider is in config - validate according to config requirements
            # Check if required API key is set for known providers
            api_key_var = self._get_api_key_var_for_provider(provider)
            if api_key_var:
                api_key_value = os.getenv(api_key_var)
                return bool(api_key_value and api_key_value.strip())

            # For providers without a predefined API key mapping,
            # check if there are any environment variable requirements in the provider config
            provider_config = provider_configs[provider]
            required_vars = []
            for _key, value in provider_config.items():
                if isinstance(value, str) and value.startswith("env:"):
                    env_var = value[4:]  # Remove "env:" prefix
                    required_vars.append(env_var)

            # Check if all required environment variables are set
            for env_var in required_vars:
                if not os.getenv(env_var):
                    return False

            return True

        except Exception:
            return False

    def get_available_models(self) -> list[str]:
        """Get list of models with API keys set."""
        try:
            config = self.config_loader.get_default_config()
            preferred_models = config.get("llm", {}).get("preferred_models", [])
            available_models = []

            DANA_LOGGER.debug(f"Checking available models from {len(preferred_models)} preferred models")

            for model in preferred_models:
                # Handle both string and dict formats
                model_name = model if isinstance(model, str) else model.get("name") if isinstance(model, dict) else None

                if model_name and self._is_model_actually_available(model_name):
                    available_models.append(model_name)

            DANA_LOGGER.debug(f"Found {len(available_models)} available models: {available_models}")
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
