"""
Agent Function Registry Integration

This module provides function registry integration for the agent system.
It handles method lookup, registration, and agent creation by delegating
to the main FUNCTION_REGISTRY.
"""

from collections.abc import Callable

from dana.registry import get_agent_type


def create_agent_instance(agent_type_name: str, field_values=None, context=None):
    """Create an agent instance (backward compatibility)."""
    from dana.core.agent.agent_instance import AgentInstance

    agent_type = get_agent_type(agent_type_name)
    if agent_type is None:
        raise ValueError(f"Agent type '{agent_type_name}' not found")
    return AgentInstance(agent_type, field_values or {})


def lookup_dana_method(receiver_type: str, method_name: str):
    """Look up a Dana method for a given receiver type and method name."""
    from dana.registry import FUNCTION_REGISTRY

    return FUNCTION_REGISTRY.lookup_struct_function(receiver_type, method_name)


def register_dana_method(receiver_type: str, method_name: str, func: Callable):
    """Register a Dana method for a given receiver type and method name."""
    from dana.registry import FUNCTION_REGISTRY

    return FUNCTION_REGISTRY.register_struct_function(receiver_type, method_name, func)


def has_dana_method(receiver_type: str, method_name: str):
    """Check if a Dana method exists for a given receiver type and method name."""
    from dana.registry import FUNCTION_REGISTRY

    return FUNCTION_REGISTRY.has_struct_function(receiver_type, method_name)
