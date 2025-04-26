"""Configuration Management for OpenDXA.

This module provides configuration management for the OpenDXA framework:

1. Agent Configuration
   - AgentConfig for managing agent settings
   - Default configuration loading
   - Environment variable overrides
   - JSON configuration file support

For detailed documentation, see:
- Configuration Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/config/README.md

Example:
    >>> from opendxa.config import AgentConfig
    >>> config = AgentConfig("my_config.json")
    >>> model = config.get("model")
"""

from opendxa.config.agent_config import AgentConfig

__all__ = [
    "AgentConfig",
] 