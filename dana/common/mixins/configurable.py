"""Base class for configurable components in Dana.

This module provides a base class for components that need configuration management.
It unifies common configuration patterns like loading from YAML, validation,
and access methods.
"""

import inspect
from pathlib import Path
from typing import Any, ClassVar, TypeVar

import yaml

from dana.common.exceptions import ConfigurationError
from dana.common.mixins.loggable import Loggable
from dana.common.utils.misc import Misc
from dana.common.utils.validation import ValidationUtilities

T = TypeVar("T")


class Configurable(Loggable):
    """Base class for configurable components in Dana.

    This class provides a unified interface for configuration management across Dana components.
    It handles loading, validating, and accessing configuration from multiple sources.

    Configuration Location:
    The configuration path is determined by the location of the class definition:
    - If MyComponent is defined in /path/to/dana/base/execution/my_component.py
    - Then its config files will be in /path/to/dana/base/execution/yaml/
    - And its default config will be in /path/to/dana/base/execution/yaml/my_component.yaml

    This means each configurable component's configuration is co-located with its code,
    making it easy to find and maintain related configurations. The default config file
    name is automatically derived from the module file name to maintain consistency with
    the physical file organization.

    Configuration Directory Structure:
    - Base path: Directory containing the class definition (e.g., /path/to/dana/base/execution/)
    - Config directory: 'yaml' subdirectory under base path (e.g., /path/to/dana/base/execution/yaml/)
    - Default config: '{module_name}.yaml' in config directory (e.g., /path/to/dana/base/execution/yaml/my_component.yaml)

    Key Features:
    - YAML file loading with defaults and overrides
    - Configuration validation
    - Path resolution for config files
    - Configuration access methods
    - Logging integration

    Usage:
        class MyComponent(Configurable):
            default_config = {
                "setting1": "default_value",
                "setting2": 42
            }

            def __init__(self, config_path=None, **overrides):
                super().__init__(config_path=config_path, **overrides)

    Configuration Sources (in order of precedence):
    1. Runtime overrides (passed as kwargs)
    2. YAML configuration file
    3. Default values (from default_config)

    Path Resolution:
    - Absolute paths: Used as-is
    - Relative paths: Resolved relative to the config directory
    - Dot notation: Converted to slashes (e.g., "planning.default" -> "planning/default.yaml")
    - File extensions: Tries .yaml and .yml if not specified

    Attributes:
        config: The current configuration dictionary
        config_path: Path to the configuration file
        default_config: Class-level default configuration
    """

    # Class-level configuration
    default_config: ClassVar[dict[str, Any]] = {}

    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for the configurable component.

        Returns:
            Path to the directory containing the class definition
        """
        return Path(inspect.getfile(cls)).parent

    @classmethod
    def get_config_path(
        cls,
        path: str | Path | None = None,
        config_dir: str = "yaml",
        default_config_file: str | None = None,
        file_extension: str = "yaml",
    ) -> Path:
        """Get path to a configuration file.

        Args:
            path: Optional path to config file
            config_dir: Directory containing config files
            default_config_file: Default config file name. If None, uses the module file name.
            file_extension: Config file extension

        Returns:
            Path to configuration file

        Raises:
            ConfigurationError: If path is invalid
        """
        try:
            # If path is None, use default config
            if path is None:
                # Use module file name as default if not specified
                if default_config_file is None:
                    module_file = inspect.getfile(cls)
                    default_config_file = Path(module_file).stem
                return cls.get_base_path() / config_dir / f"{default_config_file}.{file_extension}"

            # Convert to Path if string
            if isinstance(path, str):
                path = Path(path)

            # If path is absolute, return as is
            if path.is_absolute():
                return path

            # Handle dot notation in path (but not in filename)
            if "." in str(path):
                # Split into path parts and filename
                parts = str(path).split("/")
                # Only convert dots to slashes in path parts, not in filename
                converted_parts = []
                for part in parts[:-1]:  # All parts except the last one
                    converted_parts.append(part.replace(".", "/"))
                # Add the filename as is
                converted_parts.append(parts[-1])
                path = Path("/".join(converted_parts))

            # Check for file extension
            if not path.suffix:
                # Try with .yaml first
                yaml_path = cls.get_base_path() / config_dir / f"{path}.yaml"
                if yaml_path.exists():
                    return yaml_path

                # Then try with .yml
                yml_path = cls.get_base_path() / config_dir / f"{path}.yml"
                if yml_path.exists():
                    return yml_path

                # If neither exists, use the specified extension
                return cls.get_base_path() / config_dir / f"{path}.{file_extension}"

            # Path has extension, use as is
            return cls.get_base_path() / config_dir / path

        except Exception as e:
            raise ConfigurationError(f"Invalid config path: {path}") from e

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Configurable":
        """Create a Configurable instance from a dictionary."""
        return cls(**data)

    def __init__(self, config_path: str | Path | None = None, **overrides):
        """Initialize configurable component.

        Args:
            config_path: Optional path to config file
            **overrides: Configuration overrides

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__()
        # Initialize logger using the object's class module and name
        self.config = self._load_config(config_path)
        self._apply_overrides(overrides)
        self._validate_config()

    def _load_config(self, config_path: str | Path | None = None) -> dict[str, Any]:
        """Load configuration from YAML file or use defaults.

        Args:
            config_path: Optional path to config file

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If config file cannot be loaded
        """
        if config_path is None:
            return self.default_config.copy()

        try:
            # Get the actual config path
            actual_path = self.get_config_path(config_path)

            # Load the config from file
            file_config = Misc.load_yaml_config(actual_path)

            # Merge with defaults (file overrides defaults)
            config = self.default_config.copy()
            config.update(file_config)
            return config

        except FileNotFoundError as e:
            raise ConfigurationError(f"Configuration file not found: {config_path}") from e
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format in configuration file: {config_path}") from e
        except Exception as e:
            self.warning(f"Failed to load config: {e}. Using default configuration.")
            return self.default_config.copy()

    def _apply_overrides(self, overrides: dict[str, Any]) -> None:
        """Apply configuration overrides.

        Args:
            overrides: Dictionary of configuration overrides

        Raises:
            ConfigurationError: If overrides are invalid
        """
        try:
            self.config.update(overrides)
        except Exception as e:
            raise ConfigurationError(f"Failed to apply configuration overrides: {e}") from e

    def _validate_required(self, key: str, error_msg: str | None = None) -> None:
        """Validate that a required configuration key exists.

        Uses ValidationUtilities for centralized validation logic while maintaining
        backward compatibility with existing behavior.

        Args:
            key: Configuration key to check
            error_msg: Optional custom error message

        Raises:
            ConfigurationError: If key is missing
        """
        try:
            value = self.config.get(key)
            ValidationUtilities.validate_required_field(value=value, field_name=key, context="configuration")
        except Exception as e:
            # Use custom error message if provided, otherwise maintain original format
            if error_msg:
                raise ConfigurationError(error_msg) from e
            else:
                # Convert ValidationUtilities message to original format for backward compatibility
                raise ConfigurationError(f"Required configuration '{key}' is missing") from e

    def _validate_type(self, key: str, expected_type: type[T], error_msg: str | None = None) -> None:
        """Validate that a configuration value has the expected type.

        Uses ValidationUtilities for centralized validation logic while maintaining
        backward compatibility with existing behavior.

        Args:
            key: Configuration key to check
            expected_type: Expected type of the value
            error_msg: Optional custom error message

        Raises:
            ConfigurationError: If value has wrong type
        """
        value = self.config.get(key)
        if value is not None:  # Only validate if value exists
            try:
                ValidationUtilities.validate_type(value=value, expected_type=expected_type, field_name=key, context="configuration")
            except Exception as e:
                # Use custom error message if provided, otherwise maintain original format
                if error_msg:
                    raise ConfigurationError(error_msg) from e
                else:
                    # Convert ValidationUtilities message to original format for backward compatibility
                    raise ConfigurationError(f"Configuration '{key}' must be of type {expected_type.__name__}") from e

    def _validate_enum(self, key: str, valid_values: list[Any], error_msg: str | None = None) -> None:
        """Validate that a configuration value is in a list of valid values.

        Uses ValidationUtilities for centralized validation logic while maintaining
        backward compatibility with existing behavior.

        Args:
            key: Configuration key to check
            valid_values: List of valid values
            error_msg: Optional custom error message

        Raises:
            ConfigurationError: If value is not in valid values
        """
        value = self.config.get(key)
        if value is not None:  # Only validate if value exists
            try:
                ValidationUtilities.validate_enum(value=value, valid_values=valid_values, field_name=key, context="configuration")
            except Exception as e:
                # Use custom error message if provided, otherwise maintain original format
                if error_msg:
                    raise ConfigurationError(error_msg) from e
                else:
                    # Convert ValidationUtilities message to original format for backward compatibility
                    raise ConfigurationError(f"Configuration '{key}' must be one of {valid_values}") from e

    def _validate_path(self, key: str, must_exist: bool = True, error_msg: str | None = None) -> None:
        """Validate that a configuration value is a valid path.

        Uses ValidationUtilities for centralized validation logic while maintaining
        backward compatibility with existing behavior.

        Args:
            key: Configuration key to check
            must_exist: Whether the path must exist
            error_msg: Optional custom error message

        Raises:
            ConfigurationError: If path is invalid or doesn't exist
        """
        path_value = self.config.get(key)
        if path_value is not None:  # Only validate if value exists
            try:
                ValidationUtilities.validate_path(path=path_value, must_exist=must_exist, field_name=key, context="configuration")
            except Exception as e:
                # Use custom error message if provided, otherwise maintain original format
                if error_msg:
                    raise ConfigurationError(error_msg) from e
                else:
                    # Convert ValidationUtilities message to original format for backward compatibility
                    raise ConfigurationError(f"Invalid path '{path_value}'") from e

    def _validate_config(self) -> None:
        """Validate the current configuration.

        This method validates the base configuration structure:
        1. The base path is set and exists

        Subclasses should call super()._validate_config() before adding
        their own validation logic.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Basic structure validation
        if not isinstance(self.config, dict):
            raise ConfigurationError("Configuration must be a dictionary")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Raises:
            ConfigurationError: If value is invalid
        """
        self.config[key] = value
        self._validate_config()

    def update(self, config: dict[str, Any]) -> None:
        """Update configuration with new values.

        Args:
            config: Dictionary of new configuration values

        Raises:
            ConfigurationError: If new values are invalid
        """
        self.config.update(config)
        self._validate_config()

    def to_dict(self) -> dict[str, Any]:
        """Get the current configuration as a dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config.copy()

    def save(self, path: str | Path) -> None:
        """Save current configuration to YAML file.

        Args:
            path: Path to save configuration

        Raises:
            ConfigurationError: If configuration cannot be saved
        """
        try:
            # Get the actual path
            actual_path = self.get_config_path(path)

            # Create parent directories if they don't exist
            actual_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the config
            with open(actual_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.config, f)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {path}: {e}") from e

    @classmethod
    def get_yaml_path(cls, path: str | None = None) -> Path:
        """Get path to a configuration file.

        Args:
            path: Path to config file, which can be:
                 - A full path to a YAML file
                 - A relative path with dots (e.g., "planning.default")
                 - A relative path with slashes (e.g., "planning/default")

        Returns:
            Path to the configuration file

        Raises:
            ValueError: If path is invalid or file not found
        """
        if not path:
            # Use module file name as default if no path provided
            module_file = inspect.getfile(cls)
            default_config_file = Path(module_file).stem
            return cls.get_config_path(config_dir="yaml", default_config_file=default_config_file, file_extension="yaml")

        # Handle full paths to YAML files
        if str(path).endswith((".yaml", ".yml")):
            config_path = Path(path)
            if not config_path.exists():
                raise ValueError(f"Configuration file not found: {config_path}")
            return config_path

        # Convert dot notation to slashes if needed
        if "." in str(path) and not path.endswith(".yaml") and not path.endswith(".yml"):
            path = str(path).replace(".", "/")

        # Try both .yaml and .yml extensions
        yaml_path = cls.get_config_path(
            path=f"{path}.yaml",
            config_dir="yaml",
            default_config_file=None,  # Let get_config_path use module name
            file_extension="yaml",
        )

        if yaml_path.exists():
            return yaml_path

        yml_path = cls.get_config_path(
            path=f"{path}.yml",
            config_dir="yaml",
            default_config_file=None,  # Let get_config_path use module name
            file_extension="yaml",
        )

        if not yml_path.exists():
            raise ValueError(f"Configuration file not found: {path} (tried .yaml and .yml)")

        return yml_path

    @classmethod
    def get_prompt(cls, config_path: str | None = None, prompt_ref: str | None = None, custom_prompts: dict[str, str] | None = None) -> str:
        """Get prompt by reference.

        Args:
            config_path: Path to config file relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")
            prompt_ref: Reference to prompt in format "path/to/config.prompt_name"
                       (e.g., "default.DEFINE" or "basic/prosea.ANALYZE")
            custom_prompts: Optional custom prompts to override defaults

        Returns:
            Raw prompt text

        Raises:
            ValueError: If prompt reference is invalid
        """
        if not prompt_ref:
            return ""

        prompt_ref = str(prompt_ref)

        # Try custom prompts first
        if custom_prompts and prompt_ref in custom_prompts:
            return custom_prompts[prompt_ref]

        # Extract prompt name and config path
        if "." not in prompt_ref:
            Loggable.log_warning("Prompt reference must be in format 'config_name.prompt_name', got '%s'", prompt_ref)
            return ""

        config_path, prompt_name = prompt_ref.rsplit(".", maxsplit=1)

        try:
            # Load the config
            config = cls.load_config(path=config_path)

            # Look for the prompt in the config
            if config and "prompts" in config:
                prompts = config.get("prompts", {})
                return prompts.get(prompt_name, "")

        except Exception as e:
            Loggable.log_error("Failed to load prompt '%s': %s", prompt_ref, str(e))

        return ""

    @classmethod
    def load_config(cls, path: str | None = None) -> dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            path: Full path to config file, OR relative to the config directory
                 (e.g., "workflow/default" or "workflow/basic/prosea")

        Returns:
            Loaded configuration dictionary

        Raises:
            ConfigurationError: If configuration cannot be loaded
            ValueError: If configuration is invalid
        """
        try:
            config_path = cls.get_yaml_path(path=path)
            config = Misc.load_yaml_config(config_path)

            # Validate basic structure
            if not isinstance(config, dict):
                raise ValueError(f"Configuration must be a dictionary, got {type(config)}")

            return config

        except Exception as e:
            raise ValueError(f"Failed to load configuration from {path}: {str(e)}") from e
