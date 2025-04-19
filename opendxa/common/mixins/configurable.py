"""Base class for configurable components in DXA.

This module provides a base class for components that need configuration management.
It unifies common configuration patterns like loading from YAML, validation,
and access methods.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, ClassVar
from io import StringIO
from pathlib import Path
import inspect
import yaml
from opendxa.common.mixins.loggable import Loggable

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
        """
        if config_path is None:
            return self.default_config.copy()
            
        try:
            if isinstance(config_path, (str, Path)):
                with open(config_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                data = yaml.safe_load(StringIO(str(config_path)))
                
            # Merge with defaults
            config = self.default_config.copy()
            config.update(data)
            return config
            
        except Exception as e:
            self.warning(f"Failed to load config: {e}. Using default configuration.")
            return self.default_config.copy()
            
    def _apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply configuration overrides.
        
        Args:
            overrides: Dictionary of configuration overrides
        """
        self.config.update(overrides)
        
    def _validate_config(self) -> None:
        """Validate the current configuration.
        
        This method validates the base configuration structure:
        1. The base path is set and exists
        
        Subclasses should call super()._validate_config() before adding
        their own validation logic.
        """
        if not self.config.get("base_path"):
            self.config["base_path"] = self.get_base_path()
            
        if not Path(self.config["base_path"]).exists():
            raise ValueError(f"Base path does not exist: {self.config['base_path']}")
            
        # Basic structure validation
        if not isinstance(self.config, dict):
            raise ValueError("Configuration must be a dictionary")
        
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
        """
        self.config[key] = value
        self._validate_config()
        
    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            config: Dictionary of new configuration values
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
        """
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.config, f) 