"""
Adana Configuration Manager

Handles LLM provider configuration and environment variable management.
"""

import json
import os
from pathlib import Path
from typing import Any

import structlog


logger = structlog.get_logger()


class ConfigManager:
    """Manages LLM provider configurations."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file (defaults to adana/config.json)
        """
        if config_path is None:
            # Look for config in adana package directory
            current_dir = Path.cwd()

            # Try multiple possible locations
            possible_paths = [
                current_dir / "adana" / "config.json",  # From project root
                current_dir / "config.json",  # If already in adana dir
                Path(__file__).parent.parent.parent / "config.json",  # Relative to this file
            ]

            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            else:
                # Fallback to first option
                config_path = possible_paths[0]

        self.config_path = Path(config_path) if config_path is not None else Path("adana/config.json")
        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    config = json.load(f)
                logger.info("Loaded configuration", path=str(self.config_path))
                return config
            else:
                logger.warning("Config file not found", path=str(self.config_path))
                return {"providers": {}}
        except Exception as e:
            logger.error("Failed to load config", error=str(e), path=str(self.config_path))
            return {"providers": {}}

    def get_provider_config(self, provider: str) -> dict[str, Any] | None:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')

        Returns:
            Provider configuration dict or None if not found
        """
        return self._config.get("llm", {}).get("providers", {}).get(provider)

    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return list(self._config.get("llm", {}).get("providers", {}).keys())

    def get_provider_api_key(self, provider: str) -> str | None:
        """
        Get API key for a provider from environment variables.

        Args:
            provider: Provider name

        Returns:
            API key or None if not found
        """
        config = self.get_provider_config(provider)
        if not config:
            return None

        api_key_env = config.get("api_key_env")
        if not api_key_env:
            return None

        return os.getenv(api_key_env)

    def get_provider_base_url(self, provider: str) -> str | None:
        """
        Get base URL for a provider, checking environment variable first.

        Args:
            provider: Provider name

        Returns:
            Base URL from env var or config
        """
        config = self.get_provider_config(provider)
        if not config:
            return None

        # Check for environment variable override first
        base_url_env = config.get("base_url_env")
        if base_url_env:
            env_url = os.getenv(base_url_env)
            if env_url:
                return env_url

        # Fall back to config default
        return config.get("base_url")

    def get_provider_api_version(self, provider: str) -> str | None:
        """
        Get API version for a provider, checking environment variable first.

        Args:
            provider: Provider name

        Returns:
            API version from env var or config
        """
        config = self.get_provider_config(provider)
        if not config:
            return None

        # Check for environment variable override first
        api_version_env = config.get("api_version_env")
        if api_version_env:
            env_version = os.getenv(api_version_env)
            if env_version:
                return env_version

        # Fall back to config default
        return config.get("api_version")

    def get_provider_default_model(self, provider: str) -> str | None:
        """Get default model for a provider."""
        config = self.get_provider_config(provider)
        return config.get("default_model") if config else None

    def get_provider_models(self, provider: str) -> dict[str, str]:
        """Get available models for a provider."""
        config = self.get_provider_config(provider)
        return config.get("models", {}) if config else {}

    def is_provider_available(self, provider: str) -> bool:
        """
        Check if a provider is available (has config and API key).

        Args:
            provider: Provider name

        Returns:
            True if provider is available, False otherwise
        """
        config = self.get_provider_config(provider)
        if not config:
            return False

        # Check if API key is required and available
        api_key_env = config.get("api_key_env")
        if api_key_env and not self.get_provider_api_key(provider):
            return False

        return True

    def get_available_providers_by_priority(self) -> list[tuple[str, int]]:
        """
        Get available providers sorted by priority (highest first).

        Priority order: env var > config default

        Returns:
            List of (provider_name, priority) tuples sorted by priority
        """
        available_providers = []

        for provider_name in self.get_available_providers():
            if self.is_provider_available(provider_name):
                config = self.get_provider_config(provider_name) or {}

                # Check for priority environment variable first
                priority_env_var = f"{provider_name.upper()}_PRIORITY"
                env_priority = os.getenv(priority_env_var)

                if env_priority:
                    try:
                        priority = int(env_priority)
                    except ValueError:
                        # If env var is invalid, fall back to config
                        priority = config.get("priority", 0)
                else:
                    # Use config default
                    priority = config.get("priority", 0)

                available_providers.append((provider_name, priority))

        # Sort by priority (highest first)
        return sorted(available_providers, key=lambda x: x[1], reverse=True)

    def get_first_available_provider(self) -> str | None:
        """
        Get the first available provider by priority.

        Returns:
            Provider name or None if no providers available
        """
        available = self.get_available_providers_by_priority()
        return available[0][0] if available else None


# Global config manager instance
config_manager = ConfigManager()
