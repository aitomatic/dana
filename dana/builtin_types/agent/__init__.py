"""
Agent System for Dana Language

This module provides agent capabilities by extending the struct system.
AgentStructType inherits from StructType, and AgentStructInstance inherits from StructInstance.
"""

from .enums import (
    ConfidenceLevel,
    FSMTransitionEvent,
    PlanType,
    ProblemComplexity,
    WorkflowExecutionState,
    parse_complexity,
    parse_confidence,
    parse_plan_type,
)
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
    # Enums
    "PlanType",
    "WorkflowExecutionState",
    "FSMTransitionEvent",
    "ProblemComplexity",
    "ConfidenceLevel",
    "parse_plan_type",
    "parse_complexity",
    "parse_confidence",
]
