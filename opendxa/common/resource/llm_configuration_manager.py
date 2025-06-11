"""
LLM Configuration Manager for OpenDXA.

This module handles model selection, validation, and configuration management
for LLM resources. Extracted from LLMResource for better separation of concerns.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from typing import Any

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.exceptions import LLMError


class LLMConfigurationManager:
    """Manages LLM model configuration, selection and validation."""

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
    def selected_model(self) -> str:
        """Get the currently selected model."""
        if self._selected_model is None:
            self._selected_model = self._determine_model()
        return self._selected_model

    @selected_model.setter
    def selected_model(self, value: str) -> None:
        """Set the model, with validation."""
        if not self._validate_model(value):
            raise LLMError(f"Invalid or unavailable model: {value}")
        self._selected_model = value

    def _determine_model(self) -> str:
        """Determine which model to use based on configuration and availability."""
        # Check if we're in mock mode first to avoid unnecessary work and logging
        is_mock_mode = os.environ.get("OPENDXA_MOCK_LLM", "").lower() == "true"

        # Priority: explicit model > auto-selection > default
        if self.explicit_model:
            if self._validate_model(self.explicit_model):
                return self.explicit_model
            else:
                if is_mock_mode:
                    # In mock mode, just return a mock model instead of raising error
                    return "mock:test-model"
                raise LLMError(f"Explicitly requested model '{self.explicit_model}' is not available")

        # Try auto-selection
        auto_model = self._find_first_available_model()
        if auto_model:
            return auto_model

        # Fallback to default
        default = self._get_default_model()
        if self._validate_model(default):
            return default

        # If no models are available and we're in mock mode, return a mock model silently
        if is_mock_mode:
            return "mock:test-model"

        raise LLMError("No available LLM models found. Please check your API keys and configuration.")

    def _get_default_model(self) -> str:
        """Get the default model from configuration."""
        try:
            return self.config_loader.get_config().get("llm", {}).get("default_model", "openai:gpt-4o-mini")
        except Exception:
            return "openai:gpt-4o-mini"

    def _validate_model(self, model_name: str) -> bool:
        """Validate that a model is available and properly configured."""
        if not model_name:
            return False

        # Accept mock models when in mock mode
        if model_name.startswith("mock:"):
            return True

        try:
            provider = model_name.split(":")[0] if ":" in model_name else "openai"

            # Check for required API keys/configuration
            required_keys = {
                "openai": ["OPENAI_API_KEY"],
                "anthropic": ["ANTHROPIC_API_KEY"],
                "google": ["GOOGLE_API_KEY"],
                "cohere": ["COHERE_API_KEY"],
                "mistral": ["MISTRAL_API_KEY"],
                "groq": ["GROQ_API_KEY"],
            }

            if provider in required_keys:
                return any(os.getenv(key) for key in required_keys[provider])

            return True  # Unknown providers assumed valid

        except Exception:
            return False

    def _find_first_available_model(self) -> str | None:
        """Find the first available model from preferred list."""
        try:
            config = self.config_loader.get_config()
            preferred_models = config.get("llm", {}).get(
                "preferred_models",
                [
                    "openai:gpt-4o",
                    "openai:gpt-4o-mini",
                    "anthropic:claude-3-5-sonnet-20241022",
                    "google:gemini-1.5-pro",
                ],
            )

            for model in preferred_models:
                if self._validate_model(model):
                    return model

            return None

        except Exception:
            return None

    def get_available_models(self) -> list[str]:
        """Get list of all available models."""
        try:
            config = self.config_loader.get_config()
            all_models = config.get("llm", {}).get(
                "all_models",
                [
                    "openai:gpt-4o",
                    "openai:gpt-4o-mini",
                    "openai:gpt-4-turbo",
                    "anthropic:claude-3-5-sonnet-20241022",
                    "anthropic:claude-3-5-haiku-20241022",
                    "google:gemini-1.5-pro",
                    "google:gemini-1.5-flash",
                    "cohere:command-r-plus",
                    "mistral:mistral-large-latest",
                    "groq:llama-3.1-70b-versatile",
                ],
            )

            return [model for model in all_models if self._validate_model(model)]

        except Exception:
            return []

    def get_model_config(self, model: str | None = None) -> dict[str, Any]:
        """Get configuration for a specific model."""
        target_model = model or self.selected_model

        try:
            config = self.config_loader.get_config()
            model_configs = config.get("llm", {}).get("model_configs", {})

            # Get model-specific config or defaults
            return model_configs.get(target_model, {"max_tokens": 4096, "temperature": 0.7, "timeout": 30})

        except Exception:
            return {"max_tokens": 4096, "temperature": 0.7, "timeout": 30}
