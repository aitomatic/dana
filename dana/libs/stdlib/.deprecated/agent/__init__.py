"""
Dana Agent Stdlib Module

This module provides agent utilities and advanced agent functionality that
requires explicit import statements. Core agent functionality is available
automatically via the 'agent' keyword.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .agent_templates import agent_from_template
from .agent_utils import create_agent_pool, load_agent_config, save_agent_config, agent_benchmark, agent_metrics

__all__ = ["create_agent_pool", "agent_from_template", "load_agent_config", "save_agent_config", "agent_benchmark", "agent_metrics"]
