"""
Agent function for Dana core lib.

This module provides the core agent creation functionality that is automatically
available in all Dana programs without requiring explicit imports.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from dana.agent.agent_struct_system import AgentStructInstance, AgentStructType, register_agent_struct_type
from dana.core.lang.sandbox_context import SandboxContext


def agent_function(context: SandboxContext, name: str, fields: dict[str, Any] | None = None) -> AgentStructInstance:
    """
    Create an agent struct instance with built-in AI capabilities.

    This is the core function that powers the 'agent' keyword in Dana.
    It creates an AgentStructInstance with built-in methods like plan(), solve(),
    remember(), recall(), and chat().

    Args:
        context: The sandbox context for execution
        name: The name of the agent type to create
        fields: Optional field values for the agent instance

    Returns:
        An AgentStructInstance with built-in agent capabilities

    Example:
        # This is equivalent to: agent MyAgent: domain: str = "tech"
        my_agent = agent("MyAgent", {"domain": "tech"})

        # Use built-in methods
        plan = my_agent.plan("Solve customer issue")
        solution = my_agent.solve("System performance problem")
    """
    if fields is None:
        fields = {}

    # Create agent struct type if it doesn't exist
    agent_type = AgentStructType(name=name)
    register_agent_struct_type(agent_type)

    # Create and return agent instance
    instance = AgentStructInstance(agent_type, fields)
    return instance


# Register as a Dana function with the standard naming convention
agent_function.__name__ = "agent_function"
