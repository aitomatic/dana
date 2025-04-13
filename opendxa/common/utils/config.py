# TODO: create a Configurable base class
"""Configuration management for DXA.


This module handles loading and validating agent configurations from multiple sources:
- Default values
- YAML configuration files 
- Environment variables
- Runtime overrides

Basic Usage:
    # Load with defaults and overrides
    config = load_agent_config(
        agent_type="autonomous",
        api_key="your-key-here",
        model="gpt-4"
    )

    # Load from YAML file
    config = load_agent_config(
        agent_type="collaborative",
        config_path="agent_config.yaml"
    )

    # Load with file and overrides
    config = load_agent_config(
        agent_type="collaborative", 
        config_path="base_config.yaml",
        model="gpt-4",
        max_steps=5
    )

Configuration Sources (in order of precedence):
1. Runtime overrides (passed as kwargs)
2. YAML configuration file
3. Environment variables (e.g., OPENAI_API_KEY)
4. Default values
"""

import os
from typing import Dict, Any, Optional, List, Tuple, ClassVar
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from ..exceptions import ConfigurationError
from .configurable import Configurable

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    YAML_AVAILABLE = False

# Load .env file at module import. The usecwd=True is to forde the .env file to be in the current working directory.
load_dotenv(find_dotenv(usecwd=True), override=True)

class ConfigManager(Configurable):
    """Configuration manager for DXA."""

    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "api_key": None,
        "model": "gpt-4",
        "available_resources": [],
        "reasoning": {
            "strategy": "cot",
            "max_steps": 10
        },
        "logging": {
            "level": "INFO",
            "dir": "logs",
            "format": "text",
            "max_bytes": 1000000,
            "backup_count": 5,
            "console_output": True
        }
    }

    def __init__(self):
        """Initialize configuration manager."""
        super().__init__()
        self._yaml_cache: List[Tuple[str, Any]] = []

    def _validate_config(self) -> None:
        """Validate configuration.
        
        This method extends the base Configurable validation with agent-specific checks.
        """
        # Call base class validation first
        super()._validate_config()
        
        # Validate field types
        available_resources = self.config.get("available_resources", [])
        if not isinstance(available_resources, list):
            self.error("Invalid type for field 'resources': expected list")
            raise ConfigurationError("'resources' must be a list")
            
        reasoning = self.config.get("reasoning", {})
        if not isinstance(reasoning, dict):
            self.error("Invalid type for field 'reasoning': expected dict")
            raise ConfigurationError("'reasoning' must be a dictionary")

    def load_yaml_config(self, path: str | Path) -> Dict[str, Any]:
        """Load YAML configuration file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file does not exist
            ValueError: If config values are invalid
        """
        if not isinstance(path, Path):
            path = Path(path)

        if not path.exists():
            # Try to fix the path if it's in the form of basic/sequential/yaml.yaml
            parts = str(path).split('/')
            if len(parts) >= 3 and parts[-1] == "yaml.yaml":
                # Remove the last part and replace with the second-to-last part + .yaml
                fixed_path = '/'.join(parts[:-1]) + '.yaml'
                if Path(fixed_path).exists():
                    path = Path(fixed_path)
                else:
                    # Try removing the last two parts and replace with the second-to-last part + .yaml
                    fixed_path = '/'.join(parts[:-2]) + '/' + parts[-2] + '.yaml'
                    if Path(fixed_path).exists():
                        path = Path(fixed_path)
                    else:
                        self.error("Config file not found: %s", path)
                        raise FileNotFoundError(f"Config file not found: {path}")
            # Handle the case where the file has a .yml extension but the path is looking for .yml/yaml.yaml
            elif len(parts) >= 3 and parts[-1] == "yml.yaml":
                # Try removing the last part and replace with the second-to-last part + .yml
                fixed_path = '/'.join(parts[:-1]) + '.yml'
                if Path(fixed_path).exists():
                    path = Path(fixed_path)
                else:
                    self.error("Config file not found: %s", path)
                    raise FileNotFoundError(f"Config file not found: {path}")
            else:
                self.error("Config file not found: %s", path)
                raise FileNotFoundError(f"Config file not found: {path}")
                
        for item in self._yaml_cache:
            if item[0] == str(path):
                return item[1]

        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

            self._yaml_cache.append((str(path), config))
            if len(self._yaml_cache) > 10:
                self._yaml_cache.pop(0)

            return config

    def load_agent_config(
        self,
        agent_type: str,
        config_path: Optional[str] = None,
        **overrides
    ) -> Dict[str, Any]:
        """Load and validate agent configuration.
        
        Args:
            agent_type: Type of agent to create
            config_path: Optional path to YAML config file
            **overrides: Configuration overrides
            
        Returns:
            Dict containing agent configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
            ImportError: If pyyaml is not installed
            FileNotFoundError: If config file does not exist
            ValueError: If config values are invalid
        """
        # Start with default config
        config = self.default_config.copy()
        
        # Update with environment variables
        config["api_key"] = os.getenv("OPENAI_API_KEY")
        
        # Load from file if provided
        if config_path:
            path = Path(config_path)
            if not path.exists():
                self.error("Config file not found: %s", path)
                raise FileNotFoundError(f"Config file not found: {path}")
                
            if path.suffix not in ('.yaml', '.yml'):
                self.error("Unsupported config file type: %s", path.suffix)
                raise ConfigurationError("Config file must be .yaml or .yml")
                
            try:
                file_config = self.load_yaml_config(path)
                # Validate before updating
                self.config = file_config
                self._validate_config()
                config.update(file_config)
            except ValueError as e:
                raise ConfigurationError(str(e)) from e
                
        # Apply and validate overrides
        try:
            self.config = overrides
            self._validate_config()
            config.update(overrides)
        except ValueError as e:
            raise ConfigurationError("Invalid override values") from e
            
        # Update logging config from environment
        config["logging"] = {
            "level": str.split(os.getenv("LOG_LEVEL", "INFO"))[0],
            "dir": str.split(os.getenv("LOG_DIR", "logs"))[0],
            "format": str.split(os.getenv("LOG_FORMAT", "text"))[0],
            "max_bytes": int(str.split(os.getenv("LOG_MAX_BYTES", "1000000"))[0]),
            "backup_count": int(str.split(os.getenv("LOG_BACKUP_COUNT", "5"))[0]),
            "console_output": str.split(os.getenv("LOG_CONSOLE_OUTPUT", "true"))[0].lower() == "true"
        }
            
        self.debug("Successfully loaded config for agent type: %s", agent_type)
        return config

# Create a singleton instance
config_manager = ConfigManager()
load_yaml_config = config_manager.load_yaml_config
load_agent_config = config_manager.load_agent_config 