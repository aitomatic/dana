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

from .agent_instance import (
    AgentType,
    AgentTypeRegistry,
    AgentInstance,
    agent_type_registry,
    create_agent_instance,
    get_agent_type,
    register_agent_type,
)

__all__ = [
    "AgentType",
    "AgentInstance",
    "AgentTypeRegistry",
    "agent_type_registry",
    "register_agent_type",
    "get_agent_type",
    "create_agent_instance",
]
