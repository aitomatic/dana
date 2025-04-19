"""Agent System for OpenDXA.

This module provides the core agent implementation for the OpenDXA framework, including:
- Agent class for creating and managing intelligent agents
- AgentFactory for creating specialized agent instances
- AgentRuntime for managing agent execution
- AgentState for maintaining agent state
- Resource system for integrating external tools and services

The agent system is designed to be modular and extensible, allowing for:
- Custom agent capabilities through the capability system
- Integration of external resources through the resource system
- State management through the state system
- Input/output handling through the IO system

For detailed documentation, see:
- Agent Documentation: https://github.com/aitomatic/opendxa/blob/main/opendxa/agent/README.md

Example:
    >>> from opendxa.agent import Agent
    >>> agent = Agent()
    >>> response = agent.ask("What is quantum computing?")
"""

from opendxa.agent.agent import Agent, AgentResponse
from opendxa.agent.agent_factory import AgentFactory
from opendxa.agent.agent_runtime import AgentRuntime
from opendxa.agent.agent_state import AgentState
from opendxa.agent.resource import (
    AgentResource,
    ExpertResource,
    ResourceFactory,
)

__all__ = [
    "Agent",
    "AgentResponse",
    "AgentResource",
    "AgentRuntime",
    "AgentFactory",
    "AgentState",
    "ExpertResource",
    "ResourceFactory",
]
