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

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from dxa.common.exceptions import ConfigurationError

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    YAML_AVAILABLE = False

# Load .env file at module import. The usecwd=True is to forde the .env file to be in the current working directory.
load_dotenv(find_dotenv(usecwd=True), override=True)

logger = logging.getLogger(__name__)

def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration dictionary."""

    # Validate field types only
    resources = config.get("resources", [])
    if not isinstance(resources, list):
        logger.error("Invalid type for field 'resources': expected list")
        raise ConfigurationError("'resources' must be a list")
        
    reasoning = config.get("reasoning", {})
    if not isinstance(reasoning, dict):
        logger.error("Invalid type for field 'reasoning': expected dict")
        raise ConfigurationError("'reasoning' must be a dictionary")

_yaml_cache: List[Tuple[str, Any]] = []

def load_yaml_config(path: str | Path) -> Dict[str, Any]:
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
        logger.error("Config file not found: %s", path)
        raise FileNotFoundError(f"Config file not found: {path}")
            
    for item in _yaml_cache:
        if item[0] == str(path):
            return item[1]

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

        _yaml_cache.append((str(path), config))
        if len(_yaml_cache) > 10:
            _yaml_cache.pop(0)

        return config


# TODO: move to more appropriate module
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
            file_config = load_yaml_config(path)
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
        
    # Add logging config
    config["logging"] = {
        "level": str.split(os.getenv("LOG_LEVEL", "INFO"))[0],
        "dir": str.split(os.getenv("LOG_DIR", "logs"))[0],
        "format": str.split(os.getenv("LOG_FORMAT", "text"))[0],
        "max_bytes": int(str.split(os.getenv("LOG_MAX_BYTES", "1000000"))[0]),
        "backup_count": int(str.split(os.getenv("LOG_BACKUP_COUNT", "5"))[0]),
        "console_output": str.split(os.getenv("LOG_CONSOLE_OUTPUT", "true"))[0].lower() == "true"
    }
        
    logger.debug("Successfully loaded config for agent type: %s", agent_type)
    return config 