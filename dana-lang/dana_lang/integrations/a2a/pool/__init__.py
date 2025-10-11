"""
Agent Pool - Manages collections of A2A agents and provides selection functionality.

This package provides classes for managing pools of A2A agents and selecting
the most appropriate agent for a given task.
"""

from .agent_pool import AgentPool
from .agent_selector import AgentSelector

__all__ = ["AgentPool", "AgentSelector"]
