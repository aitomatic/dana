"""
Agent Type Registry for Dana agent types.

DEPRECATED: This module has been moved to dana.registries.type_registry.
This file is maintained for backward compatibility only.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Re-export everything from the new location
from .type_registry import (
    AgentTypeRegistry,
    global_agent_type_registry,
    create_agent_instance,
    get_agent_type,
    register_agent_type,
)

# Backward compatibility alias
agent_type_registry = global_agent_type_registry

__all__ = [
    "AgentTypeRegistry",
    "agent_type_registry",
    "global_agent_type_registry",
    "register_agent_type",
    "get_agent_type",
    "create_agent_instance",
]
