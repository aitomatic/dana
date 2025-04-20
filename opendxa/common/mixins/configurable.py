"""Base class for configurable components in DXA.

This module provides a base class for components that need configuration management.
It unifies common configuration patterns like loading from YAML, validation,
and access methods.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, ClassVar, Type, TypeVar, List
from pathlib import Path
import inspect
import yaml
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.exceptions import ConfigurationError

T = TypeVar('T')

@dataclass
class Configurable(Loggable):
    """Base class for configurable components.
    
    This class provides common configuration management functionality:
    - YAML file loading with defaults
    - Configuration validation
    - Configuration access methods
    - Logging integration
    
    Attributes:
        config: The current configuration dictionary
        config_path: Path to the configuration file
        default_config: Class-level default configuration
    """
    
    # Class-level configuration
    default_config: ClassVar[Dict[str, Any]] = {}
    
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
        path: Optional[Union[str, Path]] = None,
        config_dir: str = "yaml",
        default_config_file: str = "default",
        file_extension: str = "yaml"
    ) -> Path:
        """Get path to a configuration file.
        
        Args:
            path: Optional path to config file
            config_dir: Directory containing config files
            default_config_file: Default config file name
            file_extension: Config file extension
            
        Returns:
            Path to configuration file
            
        Raises:
            ConfigurationError: If path is invalid
        """
        try:
            # If path is None, use default config
            if path is None:
                return cls.get_base_path() / config_dir / f"{default_config_file}.{file_extension}"
            
            # Convert to Path if string
            if isinstance(path, str):
                path = Path(path)
            
            # If path is absolute, return as is
            if path.is_absolute():
                return path
            
            # If path contains dots, convert to slashes
            if "." in str(path):
                path = Path(str(path).replace(".", "/"))
            
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Configurable':
        """Create a Configurable instance from a dictionary."""
        return cls(**data)
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        **overrides
    ):
        """Initialize configurable component.
        
        Args:
            config_path: Optional path to config file
            **overrides: Configuration overrides
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__()  # Initialize Loggable
        self.config = self._load_config(config_path)
        self._apply_overrides(overrides)
        self._validate_config()
        
    def _load_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
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
            
            # Load the config
            with open(actual_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
            # Merge with defaults
            config = self.default_config.copy()
            config.update(data)
            return config
            
        except FileNotFoundError as e:
            raise ConfigurationError(f"Configuration file not found: {config_path}") from e
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format in configuration file: {config_path}") from e
        except Exception as e:
            self.warning(f"Failed to load config: {e}. Using default configuration.")
            return self.default_config.copy()
            
    def _apply_overrides(self, overrides: Dict[str, Any]) -> None:
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

    def _validate_required(self, key: str, error_msg: Optional[str] = None) -> None:
        """Validate that a required configuration key exists.
        
        Args:
            key: Configuration key to check
            error_msg: Optional custom error message
            
        Raises:
            ConfigurationError: If key is missing
        """
        if key not in self.config:
            msg = error_msg or f"Required configuration '{key}' is missing"
            raise ConfigurationError(msg)

    def _validate_type(self, key: str, expected_type: Type[T], error_msg: Optional[str] = None) -> None:
        """Validate that a configuration value has the expected type.
        
        Args:
            key: Configuration key to check
            expected_type: Expected type of the value
            error_msg: Optional custom error message
            
        Raises:
            ConfigurationError: If value has wrong type
        """
        value = self.config.get(key)
        if value is not None and not isinstance(value, expected_type):
            msg = error_msg or f"Configuration '{key}' must be of type {expected_type.__name__}"
            raise ConfigurationError(msg)

    def _validate_enum(self, key: str, valid_values: List[Any], error_msg: Optional[str] = None) -> None:
        """Validate that a configuration value is in a list of valid values.
        
        Args:
            key: Configuration key to check
            valid_values: List of valid values
            error_msg: Optional custom error message
            
        Raises:
            ConfigurationError: If value is not in valid values
        """
        value = self.config.get(key)
        if value is not None and value not in valid_values:
            msg = error_msg or f"Configuration '{key}' must be one of {valid_values}"
            raise ConfigurationError(msg)

    def _validate_path(self, key: str, must_exist: bool = True, error_msg: Optional[str] = None) -> None:
        """Validate that a configuration value is a valid path.
        
        Args:
            key: Configuration key to check
            must_exist: Whether the path must exist
            error_msg: Optional custom error message
            
        Raises:
            ConfigurationError: If path is invalid or doesn't exist
        """
        path = self.config.get(key)
        if path is not None:
            try:
                path = Path(path)
                if must_exist and not path.exists():
                    msg = error_msg or f"Path '{path}' does not exist"
                    raise ConfigurationError(msg)
            except Exception as e:
                msg = error_msg or f"Invalid path '{path}'"
                raise ConfigurationError(msg) from e
        
    def _validate_config(self) -> None:
        """Validate the current configuration.
        
        This method validates the base configuration structure:
        1. The base path is set and exists
        
        Subclasses should call super()._validate_config() before adding
        their own validation logic.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config.get("base_path"):
            self.config["base_path"] = self.get_base_path()
            
        self._validate_path("base_path", must_exist=True)
        
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
        
    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            config: Dictionary of new configuration values
            
        Raises:
            ConfigurationError: If new values are invalid
        """
        self.config.update(config)
        self._validate_config()
        
    def to_dict(self) -> Dict[str, Any]:
        """Get the current configuration as a dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
        
    def save(self, path: Union[str, Path]) -> None:
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
            with open(actual_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {path}: {e}") from e 