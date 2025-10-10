"""
Base agent implementation with common agent functionality.

This module provides the base agent class with common functionality like
resource management, agent management, workflow management, and basic
agent identity that can be shared across different agent patterns.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from adana.common.base_war import BaseWAR
from adana.common.protocols import DictParams
from adana.common.protocols.war import AgentProtocol, ResourceProtocol, WorkflowProtocol
from adana.core.global_registry import get_agent_registry


class BaseAgent(BaseWAR, AgentProtocol):
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
        self._resources: list[ResourceProtocol] = []
        self._agents: list[AgentProtocol] = []
        self._workflows: list[WorkflowProtocol] = []

        # Handle agent registration at the base level
        self._registry = registry or get_agent_registry()
        if auto_register:
            self._register_self()

    # ============================================================================
    # RESOURCE MANAGEMENT
    # ============================================================================

    def with_resources(self, *resources: ResourceProtocol) -> "BaseAgent":
        """
        Add resources to this agent using fluent interface.

        Args:
            *resources: Variable number of ResourceProtocol instances to add

        Returns:
            Self for method chaining

        Example:
            agent = BaseAgent("coordinator").with_resources(
                ToDoResource(),
                DatabaseResource(),
                WebSearchResource()
            )
        """
        self._resources.extend(resources)
        return self

    def add_resource(self, resource: ResourceProtocol) -> None:
        """
        Add a single resource to this agent.

        Args:
            resource: ResourceProtocol instance to add
        """
        self._resources.append(resource)

    def remove_resource(self, resource_id: str) -> bool:
        """
        Remove a resource by its ID.

        Args:
            resource_id: ID of the resource to remove

        Returns:
            True if resource was found and removed, False otherwise
        """
        for i, resource in enumerate(self._resources):
            if hasattr(resource, "object_id") and resource.object_id == resource_id:
                self._resources.pop(i)
                return True
        return False

    # ============================================================================
    # AGENT MANAGEMENT
    # ============================================================================

    def with_agents(self, *agents: AgentProtocol) -> "BaseAgent":
        """
        Add agents to this agent using fluent interface.

        Args:
            *agents: Variable number of AgentProtocol instances to add

        Returns:
            Self for method chaining

        Example:
            agent = BaseAgent("coordinator").with_agents(
                ResearchAgent(),
                AnalysisAgent(),
                VerifierAgent()
            )
        """
        self._agents.extend(agents)
        return self

    def add_agent(self, agent: AgentProtocol) -> None:
        """
        Add a single agent to this agent.

        Args:
            agent: AgentProtocol instance to add
        """
        self._agents.append(agent)

    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent by its ID.

        Args:
            agent_id: ID of the agent to remove

        Returns:
            True if agent was found and removed, False otherwise
        """
        for i, agent in enumerate(self._agents):
            if hasattr(agent, "object_id") and agent.object_id == agent_id:
                self._agents.pop(i)
                return True
        return False

    # ============================================================================
    # WORKFLOW MANAGEMENT
    # ============================================================================

    def with_workflows(self, *workflows: WorkflowProtocol) -> "BaseAgent":
        """
        Add workflows to this agent using fluent interface.

        Args:
            *workflows: Variable number of WorkflowProtocol instances to add

        Returns:
            Self for method chaining

        Example:
            agent = BaseAgent("coordinator").with_workflows(
                ExampleWorkflow(),
                DataProcessingWorkflow(),
                ValidationWorkflow()
            )
        """
        self._workflows.extend(workflows)
        # IMPORTANT: assign the calling agent to the workflows
        for workflow in workflows:
            workflow.agent = self
        return self

    def add_workflow(self, workflow: WorkflowProtocol) -> None:
        """
        Add a single workflow to this agent.

        Args:
            workflow: WorkflowProtocol instance to add
        """
        self._workflows.append(workflow)

    def remove_workflow(self, workflow_id: str) -> bool:
        """
        Remove a workflow by its ID.

        Args:
            workflow_id: ID of the workflow to remove

        Returns:
            True if workflow was found and removed, False otherwise
        """
        for i, workflow in enumerate(self._workflows):
            if hasattr(workflow, "object_id") and workflow.object_id == workflow_id:
                self._workflows.pop(i)
                return True
        return False

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
