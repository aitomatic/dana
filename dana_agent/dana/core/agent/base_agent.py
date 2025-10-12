"""
Base agent implementation with common agent functionality.

This module provides the base agent class with common functionality like
resource management, agent management, workflow management, and basic
agent identity that can be shared across different agent patterns.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from dana.common.base_a import BaseA
from dana.common.protocols import DictParams
from dana.common.protocols.war import AgentProtocol, ResourceProtocol, WorkflowProtocol
from dana.core.global_registry import get_agent_registry


class BaseAgent(BaseA, AgentProtocol):
    """
    Base class for all agents with common functionality.

    Provides agent identity, resource management, agent management, workflow
    management, and basic state management that can be shared across different
    agent patterns (STAR, reactive, etc.).
    """

    def __init__(self, agent_type: str | None = None, agent_id: str | None = None, auto_register: bool = True, registry=None, **kwargs):
        """
        Initialize the BaseAgent.

        Args:
            agent_type: Type of agent (e.g., 'coding', 'financial_analyst').
            agent_id: ID of the agent (defaults to None)
            auto_register: Whether to automatically register with the global registry
            registry: Specific registry to use (defaults to global registry)
            **kwargs: Additional arguments passed to mixins
        """
        # Call super() to initialize mixins with all kwargs
        kwargs |= {
            "object_id": agent_id,
        }
        super().__init__(**kwargs)
        self.agent_type = agent_type or self.__class__.__name__
        self._created_at = datetime.now().isoformat()

        # Handle agent registration at the base level
        self._registry = registry or get_agent_registry()
        if auto_register:
            self._register_self()

    # ============================================================================
    # BASIC AGENT IDENTITY
    # ============================================================================

    @property
    def agent_id(self) -> str:
        """Get the agent id."""
        return self._object_id

    @agent_id.setter
    def agent_id(self, value: str):
        """Set the agent id."""
        self._object_id = value

    @property
    def created_at(self) -> str:
        """When this agent was created."""
        return self._created_at

    def get_basic_state(self) -> dict[str, Any]:
        """Get minimal agent state for debugging and monitoring."""
        return {"object_id": self.object_id, "agent_type": self.agent_type, "created_at": self.created_at}

    # ============================================================================
    # DISCOVERY INTERFACE
    # ============================================================================

    @property
    def available_agents(self) -> Sequence[AgentProtocol]:
        """List available agents."""
        return self._agents

    @property
    def available_resources(self) -> Sequence[ResourceProtocol]:
        """List available resources."""
        return self._resources

    @property
    def available_workflows(self) -> Sequence[WorkflowProtocol]:
        """List available workflows."""
        return self._workflows

    # ============================================================================
    # QUERY INTERFACE
    # ============================================================================

    @property
    def system_prompt(self) -> str:
        """Get the system prompt of the agent."""
        return f"You are a {self.agent_type} agent."

    @property
    def private_identity(self) -> str:
        """Get the private identity of the agent."""
        return f"I am a {self.agent_type} agent with ID {self.object_id}."

    def query(self, **kwargs) -> DictParams:
        """
        Main entry point for agent interaction.

        This method provides a default implementation that can be
        overridden by subclasses to define specific agent behavior
        patterns (STAR, reactive, etc.).

        Args:
            **kwargs: The arguments to the query method.

        Returns:
            Agent response as a dictionary
        """
        return {"response": f"I am a {self.agent_type} agent, but I don't have a specific behavior pattern implemented."}

    # ============================================================================
    # AGENT REGISTRY MANAGEMENT
    # ============================================================================

    def _get_registry(self):
        """Get the agent registry."""
        return self._registry

    def _get_object_type(self) -> str:
        """Get the agent type for registry."""
        return self.agent_type

    def _get_capabilities(self) -> list[str]:
        """Get list of agent capabilities based on resources and workflows."""
        capabilities = []

        # Add capabilities based on resources (if available)
        try:
            for resource in self.available_resources:
                capabilities.append(f"resource_{resource.resource_id}")
        except AttributeError:
            # Resources not yet initialized
            pass

        # Add agent type as capability
        capabilities.append(f"agent_type_{self.agent_type}")

        return capabilities

    def _get_metadata(self) -> dict[str, Any]:
        """Get agent metadata for registry."""
        return {"config": getattr(self, "config", {})}

    def unregister_agent(self) -> bool:
        """
        Unregister this agent from the registry.

        Returns:
            True if successfully unregistered, False otherwise
        """
        return self._unregister_self()

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"BaseAgent(type={self.agent_type}, id={self.object_id})"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"BaseAgent(agent_type='{self.agent_type}', object_id='{self.object_id}')"
