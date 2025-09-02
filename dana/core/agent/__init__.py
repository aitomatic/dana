"""
Agent System for Dana Language

This module provides agent capabilities by extending the struct system.
AgentStructType inherits from StructType, and AgentStructInstance inherits from StructInstance.
"""

from .agent_instance import AgentInstance
from .agent_type import AgentType
from .function_registry import (
    create_agent_instance,
    has_dana_method,
    lookup_dana_method,
    register_dana_method,
)

__all__ = [
    # Core classes
    "AgentType",
    "AgentInstance",
    # Default methods
    # Registry functions
    "create_agent_instance",
    "lookup_dana_method",
    "register_dana_method",
    "has_dana_method",
]
