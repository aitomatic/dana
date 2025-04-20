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

from typing import Dict, Any, ClassVar
from dotenv import load_dotenv, find_dotenv
from opendxa.common.exceptions import ConfigurationError
from opendxa.common.mixins.configurable import Configurable

# Load .env file at module import. The usecwd=True is to forde the .env file to be in the current working directory.
load_dotenv(find_dotenv(usecwd=True), override=True)

class DXAConfig(Configurable):
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

    def _validate_config(self) -> None:
        """Validate configuration.
        
        This method extends the base Configurable validation with agent-specific checks.
        """
        # Call base class validation first
        super()._validate_config()
        
        # Validate field types
        available_resources = self.config.get("available_resources", [])
        if not isinstance(available_resources, list):
            self.error("Invalid type for field 'available_resources': expected list")
            raise ConfigurationError("'available_resources' must be a list")
            
        reasoning = self.config.get("reasoning", {})
        if not isinstance(reasoning, dict):
            self.error("Invalid type for field 'reasoning': expected dict")
            raise ConfigurationError("'reasoning' must be a dictionary")

# Create a singleton instance
dxa_config = DXAConfig() 