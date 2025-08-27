"""
Module agent implementation for Dana module agents.

This module provides the ModuleAgent class for wrapping Dana modules as agents.
"""

import inspect
from typing import Any

# TODO: Update to use new agent struct system
# from dana.core.builtin_types.agent_system.abstract_dana_agent import AbstractDanaAgent
from dana.integrations.a2a.server.module_agent_utils import get_module_agent_info


class ModuleAgent:  # TODO: Inherit from new agent system
    """Agent wrapper for Dana modules."""

    def __init__(self, name: str, module: Any, context: Any, **kwargs):
        """
        Initialize module agent.

        Args:
            name: Agent name
            module: The Dana module to wrap
            context: Dana execution context
            **kwargs: Additional arguments
        """
        # TODO: Update to use new agent system
        self._name = name
        self._description = kwargs.get("description", f"Module agent wrapping {getattr(module, '__name__', 'unknown')}")
        self._config = kwargs
        self.module = module
        self.context = context
        # Note: logger is provided by Loggable mixin, no need to set it

        self.debug(f"Created module agent: {self._name}")

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def agent_card(self) -> dict[str, Any]:
        """
        Agent card property to match A2A agent interface.

        Uses the module's context to automatically discover all available resources
        and their capabilities, creating a comprehensive agent card.

        Returns:
            Dictionary with agent card information including all module resources
        """
        return self.get_agent_card()

    @property
    def skills(self) -> list[dict[str, Any]]:
        return self.agent_card.get("skills", [])

    def get_agent_card(self) -> dict[str, Any]:
        """
        Generate agent card using the module's context to discover all resources.

        This method leverages the context's get_self_agent_card() to automatically
        discover all resources (like websearch, databases, APIs, etc.) that are
        available in the module and include their capabilities in the agent card.

        Returns:
            Dictionary with comprehensive agent card information
        """
        try:
            # Use the module's context to automatically discover all resources
            # This will include all tools from websearch, databases, APIs, etc.
            context_agent_card = self.context.get_self_agent_card()

            # Extract the self agent card
            if "__self__" in context_agent_card:
                base_card = context_agent_card["__self__"]
            else:
                # Fallback to basic card structure
                base_card = {"name": self.name, "description": "Module agent", "skills": [], "tags": []}

            # Enhance with module-specific information
            enhanced_card = {
                "name": base_card.get("name", self.name),
                "description": base_card.get("description", f"Module agent wrapping {self.module.__name__}"),
                "type": "module_agent",
                "module_name": getattr(self.module, "__name__", "unknown"),
                "capabilities": ["solve"],  # All module agents have solve capability
                "skills": base_card.get("skills", []),
                "tags": base_card.get("tags", []),
                "resource_count": len(self.context.list_resources()),
                "available_resources": self.context.list_resources(),
            }

            self.debug(
                f"Generated agent card for {self.name} with {len(enhanced_card['skills'])} skills from {enhanced_card['resource_count']} resources"
            )
            return enhanced_card

        except Exception as e:
            self.warning(f"Failed to generate agent card using context resources: {e}")
            # Fallback to basic agent card
            agent_info = get_module_agent_info(self.module)
            return {
                "name": agent_info["agent_name"],
                "description": agent_info["agent_description"],
                "type": "module_agent",
                "module_name": getattr(self.module, "__name__", "unknown"),
                "capabilities": ["solve"],
                "skills": [],
                "tags": [],
                "resource_count": 0,
                "available_resources": [],
            }

    def refresh_agent_card(self) -> None:
        """
        Refresh agent card (re-discovers resources in case they changed).
        """
        self.debug(f"Refreshed agent card for module agent {self.name}")

    async def solve(self, task: str) -> str:
        """
        Solve a task using the module's solve function.

        Args:
            task: The task to solve

        Returns:
            The solution from the module
        """
        try:
            self.debug(f"Module agent {self.name} solving task: {task}")

            # Get the solve function from the module
            solve_func = self.module.solve

            # For Dana functions, we need to call them with proper context
            # so they have access to module variables like websearch
            from dana.core.lang.interpreter.functions.dana_function import DanaFunction

            if isinstance(solve_func, DanaFunction):
                # Call Dana function with its original context
                # This ensures access to module variables like websearch
                result = solve_func(task)
            else:
                # Handle regular Python functions
                if inspect.iscoroutinefunction(solve_func):
                    result = await solve_func(task)
                else:
                    result = solve_func(task)

            self.debug(f"Module agent {self.name} completed task")
            return str(result)

        except Exception as e:
            error_msg = f"Module agent {self.name} failed to solve task: {e}"
            self.error(error_msg)
            raise RuntimeError(error_msg) from e
