"""Agent configuration management."""

import json
import os
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from dana.common.config.config_loader import ConfigLoader
from dana.common.mixins.loggable import Loggable


class AgentConfig(BaseModel, Loggable):
    """Agent configuration with defaults and loading logic."""

    # Default configuration will be loaded from file
    DEFAULT_CONFIG: ClassVar[dict[str, Any]] = None

    # Model fields
    max_tokens: int = Field(default=2000)
    model: str | None = Field(default=None)
    temperature: float = Field(default=0.7)
    preferred_models: list = Field(default_factory=list)
    logging: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, config_path: str | None = None, **overrides):
        """Initialize agent configuration.

        Args:
            config_path: Optional path to JSON config file
            **overrides: Configuration overrides
        """
        # Load default config if not already loaded
        if self.__class__.DEFAULT_CONFIG is None:
            self.__class__.DEFAULT_CONFIG = self._load_default_config()

        # Start with default config
        config = self.__class__.DEFAULT_CONFIG.copy()

        # Load from file if provided
        if config_path:
            self._load_from_file(config_path)

        # Apply overrides
        config.update(overrides)

        # Extract preferred_models from llm section
        if "llm" in config and "preferred_models" in config["llm"]:
            config["preferred_models"] = config["llm"]["preferred_models"]
            self.debug("Using preferred_models from config file (llm section).")
        else:
            config["preferred_models"] = []
            self.debug("No preferred_models found in llm section, using empty list.")

        # Initialize parent class with config
        super().__init__(**config)

        # Find and set the first available model
        self.debug("Finding first available model...")
        self.model = self._find_first_available_model()
        self.debug(f"Selected model: {self.model}")

        # Update logging config from environment
        self._update_logging_from_env()

    def _load_default_config(self) -> dict[str, Any]:
        """Load default configuration from JSON file.

        Returns:
            Dictionary containing the default configuration

        Raises:
            FileNotFoundError: If default config file cannot be found
            ValueError: If file is not JSON or JSON is invalid
        """
        return ConfigLoader().get_default_config()

    def _find_first_available_model(self) -> str | None:
        """Find the first available model based on environment variables.

        Returns:
            Name of the first model that has all required environment variables available, or None if no models are available
        """
        self.debug("Checking available environment variables for model selection...")

        # Handle both old format (list of dicts) and new format (list of strings)
        for model_config in self.preferred_models:
            if isinstance(model_config, dict):
                # Old format: list of dictionaries
                model_name = model_config["name"]
                required_vars = model_config.get("required_env_vars", [])
            else:
                # New format: list of strings
                model_name = model_config
                required_vars = self._get_required_env_vars_for_model(model_name)

            self.debug(f"Checking model {model_name} with required vars: {required_vars}")

            # Check if all required environment variables are available
            available_vars = {var: bool(os.getenv(var)) for var in required_vars}
            self.debug(f"Available vars: {available_vars}")

            if all(available_vars.values()):
                self.debug(f"Found available model: {model_name}")
                return model_name

        # If we get here, no models are available - return None
        self.warning("No models found with available environment variables")
        return None

    def _get_required_env_vars_for_model(self, model_name: str) -> list[str]:
        """Get required environment variables for a model based on its provider.

        Args:
            model_name: Model name in format "provider:model" or just "provider"

        Returns:
            List of required environment variable names
        """
        # Extract provider from model name
        if ":" in model_name:
            provider = model_name.split(":")[0]
        else:
            provider = model_name

        # Map providers to their required environment variables
        provider_env_map = {
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
            "google": ["GOOGLE_API_KEY"],
            "deepseek": ["DEEPSEEK_API_KEY"],
            "cohere": ["COHERE_API_KEY"],
            "azure": ["AZURE_OPENAI_API_KEY"],
            "ibm_watsonx": ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"],
            "local": ["LOCAL_API_KEY"],  # Optional for local models
        }

        return provider_env_map.get(provider, [])

    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from JSON file.

        Searches for the config file in the following order:
        1. Exact path provided
        2. Relative to the config directory
        3. Current working directory

        Args:
            config_path: Path to JSON config file

        Raises:
            FileNotFoundError: If config file cannot be found
            ValueError: If file is not JSON or JSON is invalid
        """
        # Convert to Path if string
        path = Path(config_path)

        # Check file extension
        if path.suffix != ".json":
            raise ValueError("Config file must be .json")

        # Try exact path first
        if path.exists():
            return self._load_json_file(path)

        # Try relative to config directory
        config_dir = Path(__file__).parent
        config_file_path = config_dir / path
        if config_file_path.exists():
            return self._load_json_file(config_file_path)

        # Try current working directory
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            return self._load_json_file(cwd_path)

        # If we get here, file wasn't found in any location
        raise FileNotFoundError(
            f"Config file not found in any location: {config_path}\nTried:\n1. {path}\n2. {config_dir / path}\n3. {Path.cwd() / path}"
        )

    def _load_json_file(self, path: Path) -> None:
        """Load and update configuration from a JSON file.

        Args:
            path: Path to JSON file

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            with open(path, encoding="utf-8") as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    setattr(self, key, value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {path}") from e
        except Exception as e:
            raise ValueError(f"Failed to load config from {path}") from e

    def _update_logging_from_env(self) -> None:
        """Update logging configuration from environment variables."""

        # Helper function to safely convert string to int
        def safe_int(value: str, default: int) -> int:
            try:
                # Remove any comments and whitespace
                clean_value = value.split("#")[0].strip()
                return int(clean_value) if clean_value else default
            except (ValueError, AttributeError):
                return default

        self.logging = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "dir": os.getenv("LOG_DIR", "logs"),
            "format": os.getenv("LOG_FORMAT", "text"),
            "max_bytes": safe_int(os.getenv("LOG_MAX_BYTES", "1000000"), 1000000),
            "backup_count": safe_int(os.getenv("LOG_BACKUP_COUNT", "5"), 5),
            "console_output": os.getenv("LOG_CONSOLE_OUTPUT", "true").lower() == "true",
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self, key, default)

    def update(self, config: dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in config.items():
            setattr(self, key, value)
