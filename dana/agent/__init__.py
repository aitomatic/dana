"""
Dana Agent System

This module implements the native agent keyword for Dana language with built-in
intelligence capabilities including memory, knowledge, and communication.

The agent system is now unified with the struct system through inheritance:
- AgentStructType inherits from StructType
- AgentStructInstance inherits from StructInstance

Design Reference: dana/agent/.design/3d_methodology_agent_struct_unification.md

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .agent_struct_system import (
    AgentStructInstance,
    AgentStructType,
    AgentStructTypeRegistry,
    agent_struct_type_registry,
    create_agent_struct_instance,
    get_agent_struct_type,
    register_agent_struct_type,
)

__all__ = [
    "AgentStructType",
    "AgentStructInstance",
    "AgentStructTypeRegistry",
    "agent_struct_type_registry",
    "register_agent_struct_type",
    "get_agent_struct_type",
    "create_agent_struct_instance",
]
