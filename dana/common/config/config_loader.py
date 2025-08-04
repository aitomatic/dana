"""Configuration loading and management for Dana.

This module provides centralized configuration management using the ConfigLoader
class. It supports loading configuration from 'dana_config.json' with a
defined search hierarchy and allows overriding via the DANA_CONFIG environment
variable.

Search Hierarchy for 'dana_config.json':
1. DANA_CONFIG environment variable (absolute path override)
2. Current Working Directory (./dana_config.json) - project override
3. User Home Directory (~/.dana/dana_config.json) - user global config
4. Dana Library Directory (dana/dana_config.json) - default fallback

Features:
- Singleton pattern for consistent config access
- Hierarchical search with user override support
- Clear error handling with detailed location reporting
- Environment variable override capability

Example:
    # Get config using the default search hierarchy
    loader = ConfigLoader()
    config = loader.get_default_config()

    # Override with environment variable
    # export DANA_CONFIG=/path/to/my_config.json
    # python my_script.py
"""

import json
import os
from pathlib import Path
from typing import Any

from dana.common.exceptions import ConfigurationError
from dana.common.mixins.loggable import Loggable


class ConfigLoader(Loggable):
    """Centralized configuration loader with hierarchical search and environment variable support.

    Implements the singleton pattern for consistent access. Loads configuration
    from 'dana_config.json' based on a search hierarchy that allows user overrides.

    Search Hierarchy for 'dana_config.json' (used by get_default_config):
    1. DANA_CONFIG environment variable (absolute path override)
    2. Current Working Directory (./dana_config.json) - project override
    3. User Home Directory (~/.dana/dana_config.json) - user global config
    4. Dana Library Directory (dana/dana_config.json) - default fallback

    This design allows users to override the default configuration at multiple levels:
    - Environment variable for absolute control
    - Project directory for project-specific settings
    - Home directory for user global preferences
    - Library directory as the ultimate fallback

    Attributes:
        _instance: Singleton instance of the ConfigLoader.
        DEFAULT_CONFIG_FILENAME: The standard name for the configuration file.

    Example:
        >>> loader = ConfigLoader()
        >>> # Loads config based on search hierarchy
        >>> config = loader.get_default_config()

        >>> # Load a specific config file from the library directory
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
            self._cached_config = None  # Cache for the default config
            self.debug("ConfigLoader initialized")
            self._initialized = True
        else:
            self.debug("ConfigLoader already initialized (singleton)")

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
                config = json.load(f)
                return config
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {path}") from e
        except Exception as e:
            # Catch other potential issues like permission errors
            raise ConfigurationError(f"Failed to load config from {path}: {e}") from e

    def get_default_config(self) -> dict[str, Any]:
        """Gets the default configuration following the search hierarchy.

        Searches for and loads 'dana_config.json' based on the following hierarchy:
        1. DANA_CONFIG environment variable (absolute path override)
        2. Current Working Directory (./dana_config.json) - project override
        3. User Home Directory (~/.dana/dana_config.json) - user global config
        4. Dana Library Directory (dana/dana_config.json) - default fallback

        This allows users to override the default configuration at multiple levels,
        from project-specific settings to user global preferences.

        The configuration is cached after the first load to improve performance
        and avoid repeated file I/O operations.

        Returns:
            A dictionary containing the loaded default configuration.

        Raises:
            ConfigurationError: If no configuration file is found in any of the
                                specified locations or if loading/parsing fails.
        """
        # Return cached config if available
        if self._cached_config is not None:
            return self._cached_config

        config_path_env = os.getenv("DANA_CONFIG")

        # 1. Check Environment Variable
        if config_path_env:
            env_path = Path(config_path_env).resolve()
            try:
                config = self._load_config_from_path(env_path)
                self._cached_config = config  # Cache the result
                return config
            except ConfigurationError as e:
                # Raise specific error if env var path fails
                raise ConfigurationError(f"Failed to load config from DANA_CONFIG ({env_path}): {e}")

        # 2. Check Current Working Directory
        cwd_path = Path.cwd() / self.DEFAULT_CONFIG_FILENAME
        if cwd_path.is_file():
            # No try-except here, let _load_config_from_path handle errors
            config = self._load_config_from_path(cwd_path)
            self._cached_config = config  # Cache the result
            return config

        # 3. Check User's Home Directory (~/.dana/)
        home_path = Path.home() / ".dana" / self.DEFAULT_CONFIG_FILENAME
        if home_path.is_file():
            # No try-except here, let _load_config_from_path handle errors
            config = self._load_config_from_path(home_path)
            self._cached_config = config  # Cache the result
            return config

        # 4. Check Dana Library Directory (default config)
        lib_path = self.config_dir / self.DEFAULT_CONFIG_FILENAME
        if lib_path.is_file():
            # No try-except here, let _load_config_from_path handle errors
            config = self._load_config_from_path(lib_path)
            self._cached_config = config  # Cache the result
            return config

        # If not found anywhere
        raise ConfigurationError(
            f"Default config '{self.DEFAULT_CONFIG_FILENAME}' not found.\n"
            f"Checked locations:\n"
            f"- DANA_CONFIG environment variable: (not set or failed)\n"
            f"- Current Working Directory: {cwd_path}\n"
            f"- User Home Directory: {home_path}\n"
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

    def clear_cache(self) -> None:
        """Clear the cached configuration.

        This forces the next call to get_default_config() to reload the config
        from disk. Useful for testing or when config files might have changed.
        """
        self._cached_config = None
        self.debug("Config cache cleared")
