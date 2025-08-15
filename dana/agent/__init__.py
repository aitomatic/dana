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

from dana.registries.type_registry import (
    AgentTypeRegistry,
    create_agent_instance,
    get_agent_type,
    global_agent_type_registry,
    register_agent_type,
)

from .agent_instance import (
    AgentInstance,
    AgentType,
)

__all__ = [
    "AgentInstance",
    "AgentType",
    "AgentTypeRegistry",
    "global_agent_type_registry",
    "create_agent_instance",
    "get_agent_type",
    "register_agent_type",
]
