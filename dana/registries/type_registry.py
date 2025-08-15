"""
Type Registry for Dana

This module re-exports type registry functionality from the new global registry system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Re-export from the new global registry system
from dana.registry import (
    TypeRegistry,
    get_agent_type,
    get_global_registry,
    get_resource_type,
    get_struct_type,
    register_agent_type,
    register_resource_type,
    register_struct_type,
)

# Create convenience instances for backward compatibility
global_agent_type_registry = get_global_registry()
global_resource_type_registry = get_global_registry()
global_struct_type_registry = get_global_registry()
agent_type_registry = global_agent_type_registry

# Re-export the registry classes from the new system
AgentTypeRegistry = TypeRegistry
ResourceTypeRegistry = TypeRegistry
StructTypeRegistry = TypeRegistry


# Backward compatibility function
def create_agent_instance(name, field_values=None, context=None):
    """Create an agent instance (backward compatibility)."""
    from dana.agent import AgentInstance

    agent_type = get_agent_type(name)
    if agent_type is None:
        raise ValueError(f"Agent type '{name}' not found")
    return AgentInstance(agent_type, field_values or {})


__all__ = [
    "AgentTypeRegistry",
    "ResourceTypeRegistry",
    "StructTypeRegistry",
    "global_agent_type_registry",
    "global_resource_type_registry",
    "global_struct_type_registry",
    "agent_type_registry",
    "register_agent_type",
    "get_agent_type",
    "create_agent_instance",
    "register_resource_type",
    "get_resource_type",
    "register_struct_type",
    "get_struct_type",
]
