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
from opendxa.common.utils.validation import ValidationUtilities


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

        # If no models are available and we're in mock mode, return a mock model silently
        if is_mock_mode:
            return "mock:test-model"

        raise LLMError("No available LLM models found. Please check your API keys and configuration.")

    def _validate_model(self, model_name: str) -> bool:
        """Validate that a model is available and properly configured.

        Uses ValidationUtilities for centralized validation logic while maintaining
        backward compatibility with existing behavior.
        """
        if not model_name:
            return False

        # Accept mock models when in mock mode
        if model_name.startswith("mock:"):
            return True

        try:
            # Check if the provider exists in configuration
            provider = self._get_provider_from_model(model_name)
            if provider:
                config = self.config_loader.get_default_config()
                provider_configs = config.get("llm", {}).get("provider_configs", {})

                # If provider is not in config, model is invalid
                if provider not in provider_configs:
                    return False

            # For model validation, we only check required API keys, not whether
            # the model is in the preferred_models list. The preferred_models list
            # is used for selection priority, not validation restrictions.
            required_env_vars = self._get_required_env_vars_for_model(model_name)

            # Use ValidationUtilities for the actual validation
            # Pass None for available_models to skip that check
            return ValidationUtilities.validate_model_availability(
                model_name=model_name, available_models=None, required_env_vars=required_env_vars, context="LLM configuration"
            )

        except Exception:
            # Maintain original behavior: return False on any exception
            return False

    def _get_available_models_list(self) -> list[str] | None:
        """Get the list of available models from configuration.

        Returns None to indicate that any model name should be accepted
        (ValidationUtilities will only check environment variables).
        """
        try:
            config = self.config_loader.get_default_config()

            # Load preferred_models from llm section
            if "llm" in config and "preferred_models" in config["llm"]:
                preferred_models = config["llm"]["preferred_models"]
            else:
                preferred_models = []

            # Extract model names from both string and dict formats
            model_names = []
            for model in preferred_models:
                if isinstance(model, str):
                    model_names.append(model)
                elif isinstance(model, dict) and model.get("name"):
                    model_names.append(model["name"])

            # Return None if no models found - this means "accept any model name"
            return model_names if model_names else None

        except Exception:
            return None

    def _get_required_env_vars_for_model(self, model_name: str) -> list[str]:
        """Get required environment variables for a specific model based on provider configs."""
        try:
            # Get configuration
            config = self.config_loader.get_default_config()

            # Load provider_configs from llm section
            if "llm" in config and "provider_configs" in config["llm"]:
                provider_configs = config["llm"]["provider_configs"]
            else:
                return []

            # Determine provider from model name
            provider = self._get_provider_from_model(model_name)

            if not provider or provider not in provider_configs:
                return []

            # Get provider config
            provider_config = provider_configs[provider]

            # Extract required environment variables from provider config
            required_vars = []
            for key, value in provider_config.items():
                if isinstance(value, str) and value.startswith("env:"):
                    env_var = value[4:]  # Remove "env:" prefix
                    required_vars.append(env_var)

            return required_vars

        except Exception:
            return []

    def _get_provider_from_model(self, model_name: str) -> str | None:
        """Extract provider name from model name."""
        if model_name == "local":
            return "local"
        elif ":" in model_name:
            return model_name.split(":", 1)[0]
        else:
            return None

    def _find_first_available_model(self) -> str | None:
        """Find the first available model from preferred list."""
        try:
            config = self.config_loader.get_default_config()

            # Load preferred_models from llm section
            if "llm" in config and "preferred_models" in config["llm"]:
                preferred_models = config["llm"]["preferred_models"]
            else:
                # No preferred models configured
                return None

            for model in preferred_models:
                # Handle string format (new streamlined approach)
                if isinstance(model, str):
                    model_name = model
                # Handle dict format (backward compatibility)
                elif isinstance(model, dict):
                    model_name = model.get("name")
                else:
                    continue

                if model_name and self._validate_model(model_name):
                    return model_name

            return None

        except Exception:
            return None

    def get_available_models(self) -> list[str]:
        """Get list of all available models."""
        try:
            config = self.config_loader.get_default_config()

            # Get models from preferred_models (new streamlined approach)
            preferred_models = config.get("llm", {}).get("preferred_models", [])
            preferred_model_names = []

            for model in preferred_models:
                # Handle string format (new streamlined approach)
                if isinstance(model, str):
                    preferred_model_names.append(model)
                # Handle dict format (backward compatibility)
                elif isinstance(model, dict) and model.get("name"):
                    preferred_model_names.append(model["name"])

            # Also get models from all_models if it exists (backward compatibility)
            all_models = config.get("llm", {}).get("all_models", [])

            # Combine both lists, removing duplicates while preserving order
            combined_models = []
            seen_models = set()

            # Add preferred models first (they have priority)
            for model in preferred_model_names:
                if model not in seen_models:
                    combined_models.append(model)
                    seen_models.add(model)

            # Add all_models that aren't already included
            for model in all_models:
                if model not in seen_models:
                    combined_models.append(model)
                    seen_models.add(model)

            return [model for model in combined_models if self._validate_model(model)]

        except Exception:
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
