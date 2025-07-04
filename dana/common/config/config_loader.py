"""Configuration loading and management for Dana.

This module provides centralized configuration management using the ConfigLoader
class. It supports loading configuration from 'dana_config.json' with a
defined search order and allows overriding via the DANA_CONFIG environment
variable.

Features:
- Singleton pattern for consistent config access
- Standardized path resolution for config files
- Search order for 'dana_config.json': DANA_CONFIG env var -> CWD -> Project Root
- Clear error handling for config loading failures

Example:
    # Get config using the default search order
    loader = ConfigLoader()
    config = loader.get_default_config()

    # If DANA_CONFIG is set, it overrides the search order:
    # export DANA_CONFIG=/path/to/my_config.json
    # python my_script.py
    # Now loader.get_default_config() will load from /path/to/my_config.json
"""

import json
import os
from pathlib import Path
from typing import Any

from dana.common.exceptions import ConfigurationError
from dana.common.mixins.loggable import Loggable


class ConfigLoader(Loggable):
    """Centralized configuration loader with environment variable support and search order.

    Implements the singleton pattern for consistent access. Loads configuration
    from 'dana_config.json' based on a search hierarchy that allows user overrides.

    Search Hierarchy for 'dana_config.json' (used by get_default_config):
    1. Path specified by the DANA_CONFIG environment variable.
    2. 'dana_config.json' in the Current Working Directory (CWD) - user override.
    3. 'dana_config.json' in the dana library directory - default config.

    This design allows users of the Dana library to override the default configuration
    by placing their own dana_config.json in their project directory, while falling
    back to the library's default configuration if no user override is found.

    Attributes:
        _instance: Singleton instance of the ConfigLoader.
        DEFAULT_CONFIG_FILENAME: The standard name for the configuration file.

    Example:
        >>> loader = ConfigLoader()
        >>> # Loads config based on DANA_CONFIG, CWD, or library default
        >>> config = loader.get_default_config()

        >>> # Load a specific, non-default config file from the library directory
        >>> other_config = loader.load_config("other_settings.json")
    """

    _instance = None
    DEFAULT_CONFIG_FILENAME = "dana_config.json"

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the ConfigLoader instance.

        Only initializes once due to singleton pattern.
        """
        # Check if already initialized to avoid double initialization
        if not hasattr(self, "_initialized"):
            super().__init__()  # Initialize Loggable mixin
            self._initialized = True

    @property
    def config_dir(self) -> Path:
        """Get the dana library directory (where default config is stored).

        Returns:
            Path object pointing to the dana library directory.

        Example:
            >>> loader = ConfigLoader()
            >>> lib_dir = loader.config_dir
            >>> print(lib_dir) # doctest: +SKIP
            /path/to/dana
        """
        # Assumes this file is in dana/common/config/
        # Go up 2 levels: config -> common -> dana
        return Path(__file__).parent.parent.parent

    def _load_config_from_path(self, path: Path) -> dict[str, Any]:
        """Loads and parses a JSON configuration file from a specific path.

        Args:
            path: The absolute Path object pointing to the config file.

        Returns:
            A dictionary containing the loaded configuration.

        Raises:
            ConfigurationError: If the file doesn't exist, isn't a file,
                                or contains invalid JSON.
        """
        if not path.is_file():
            raise ConfigurationError(f"Config path does not point to a valid file: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {path}") from e
        except Exception as e:
            # Catch other potential issues like permission errors
            raise ConfigurationError(f"Failed to load config from {path}: {e}") from e

    def get_default_config(self) -> dict[str, Any]:
        """Gets the default configuration following the search hierarchy.

        Searches for and loads 'dana_config.json' based on the following order:
        1. Path specified by the DANA_CONFIG environment variable.
        2. 'dana_config.json' in the Current Working Directory (CWD) - user override.
        3. 'dana_config.json' in the dana library directory - default config.

        This allows users to override the library's default configuration by placing
        their own dana_config.json in their project directory.

        Returns:
            A dictionary containing the loaded default configuration.

        Raises:
            ConfigurationError: If no configuration file is found in any of the
                                specified locations or if loading/parsing fails.
        """
        config_path_env = os.getenv("DANA_CONFIG")

        # 1. Check Environment Variable
        if config_path_env:
            env_path = Path(config_path_env).resolve()
            self.debug(f"Attempting to load config from DANA_CONFIG: {env_path}")
            try:
                return self._load_config_from_path(env_path)
            except ConfigurationError as e:
                # Raise specific error if env var path fails
                raise ConfigurationError(f"Failed to load config from DANA_CONFIG ({env_path}): {e}")

        # 2. Check Current Working Directory
        cwd_path = Path.cwd() / self.DEFAULT_CONFIG_FILENAME
        if cwd_path.is_file():
            self.debug(f"Attempting to load config from CWD: {cwd_path}")
            # No try-except here, let _load_config_from_path handle errors
            return self._load_config_from_path(cwd_path)

        # 3. Check Dana Library Directory (default config)
        lib_path = self.config_dir / self.DEFAULT_CONFIG_FILENAME
        if lib_path.is_file():
            self.debug(f"Attempting to load config from library directory: {lib_path}")
            # No try-except here, let _load_config_from_path handle errors
            return self._load_config_from_path(lib_path)

        # If not found anywhere
        raise ConfigurationError(
            f"Default config '{self.DEFAULT_CONFIG_FILENAME}' not found.\n"
            f"Checked locations:\n"
            f"- DANA_CONFIG environment variable: (not set or failed)\n"
            f"- Current Working Directory: {cwd_path}\n"
            f"- Dana Library Directory: {lib_path}"
        )

    def load_config(self, config_name: str) -> dict[str, Any]:
        """Loads a specific configuration file relative to the dana library directory.

        This method is intended for loading secondary configuration files,
        not the main 'dana_config.json' (use get_default_config for that).

        Args:
            config_name: The name of the configuration file (e.g., 'tool_settings.json').

        Returns:
            A dictionary containing the loaded configuration.

        Raises:
            ConfigurationError: If the config file cannot be loaded or parsed.

        Example:
            >>> loader = ConfigLoader()
            >>> tool_config = loader.load_config("tool_settings.json") # Looks for dana/tool_settings.json
        """
        config_path = self.config_dir / config_name
        return self._load_config_from_path(config_path)
