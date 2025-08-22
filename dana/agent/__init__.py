"""
Dana Agent System

This module implements the native agent keyword for Dana language with built-in
intelligence capabilities including memory, knowledge, and communication.

The agent system is now unified with the struct system through inheritance:
- AgentStructType inherits from StructType
- AgentStructInstance inherits from StructInstance

Design Reference: dana/agent/.design/3d_methodology_agent_instance_unification.md

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# For backward compatibility, create aliases
from dana.registry import TypeRegistry as AgentTypeRegistry
from dana.registry import (
    get_agent_type,
    register_agent_type,
)


# Create backward compatibility functions and instances
def create_agent_instance(agent_type_name: str, field_values=None, context=None):
    """Create an agent instance (backward compatibility)."""
    from dana.agent.agent_instance import AgentInstance

    agent_type = get_agent_type(agent_type_name)
    if agent_type is None:
        raise ValueError(f"Agent type '{agent_type_name}' not found")
    return AgentInstance(agent_type, field_values or {})


from .agent_instance import (
    AgentInstance,
    AgentType,
)

__all__ = [
    "AgentInstance",
    "AgentType",
    "AgentTypeRegistry",
    "create_agent_instance",
    "get_agent_type",
    "register_agent_type",
]
