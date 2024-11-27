"""Configuration utilities for DXA."""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from dxa.common.errors import ConfigurationError

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration dictionary.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate required fields
    if not config.get("api_key"):
        logger.error("Missing required field: api_key")
        raise ConfigurationError("API key is required")
        
    # Validate field types
    resources = config.get("resources", [])
    if not isinstance(resources, list):
        logger.error("Invalid type for field 'resources': expected list")
        raise ConfigurationError("'resources' must be a list")
        
    reasoning = config.get("reasoning", {})
    if not isinstance(reasoning, dict):
        logger.error("Invalid type for field 'reasoning': expected dict")
        raise ConfigurationError("'reasoning' must be a dictionary")

def _load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ImportError: If PyYAML is not installed
        ConfigurationError: If YAML is invalid
    """
    if not YAML_AVAILABLE:
        logger.error("PyYAML is required but not installed")
        raise ImportError(
            "PyYAML is required for configuration files. "
            "Install with: pip install pyyaml"
        )
    try:
        yaml_config = yaml.safe_load(path.read_text())
        if not isinstance(yaml_config, dict):
            raise ValueError("YAML config must be a dictionary")
        return yaml_config
    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML config: %s", str(e))
        raise ConfigurationError(f"Invalid YAML format in {path}") from e

def load_agent_config(
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
    # Load defaults
    config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4",
        "resources": [],
        "reasoning": {
            "strategy": "cot",
            "max_steps": 10
        }
    }
    
    # Load from file if provided
    if config_path:
        path = Path(config_path)
        if not path.exists():
            logger.error("Config file not found: %s", path)
            raise FileNotFoundError(f"Config file not found: {path}")
            
        if path.suffix not in ('.yaml', '.yml'):
            logger.error("Unsupported config file type: %s", path.suffix)
            raise ConfigurationError("Config file must be .yaml or .yml")
            
        try:
            file_config = _load_yaml_config(path)
            # Validate before updating
            _validate_config(file_config)
            config.update(file_config)
        except ValueError as e:
            raise ConfigurationError(str(e)) from e
            
    # Apply and validate overrides
    try:
        _validate_config(overrides)
        config.update(overrides)
    except ValueError as e:
        raise ConfigurationError("Invalid override values") from e
        
    # Final validation of complete config
    _validate_config(config)
        
    logger.debug("Successfully loaded config for agent type: %s", agent_type)
    return config 