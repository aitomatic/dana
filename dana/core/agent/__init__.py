"""
Agent System for Dana Language

This module provides agent capabilities by extending the struct system.
AgentStructType inherits from StructType, and AgentStructInstance inherits from StructInstance.
"""

from .agent_instance import AgentInstance
from .agent_type import AgentType
from .agent_state import AgentState
from .context import ProblemContext, ExecutionContext
from .mind import AgentMind
from .capabilities import CapabilityRegistry
from .utils import (
    create_agent_instance,
    has_dana_method,
    lookup_dana_method,
    register_dana_method,
)

__all__ = [
    # Core classes
    "AgentType",
    "AgentInstance",
    "AgentState",
    # Context and subsystems
    "ProblemContext",
    "ExecutionContext",
    "AgentMind",
    "CapabilityRegistry",
    # Registry functions
    "create_agent_instance",
    "lookup_dana_method",
    "register_dana_method",
    "has_dana_method",
]
