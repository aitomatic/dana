"""Agent resource implementation."""

import asyncio
from typing import Dict, Any

from dxa.core.resource.base_resource import BaseResource
from dxa.common.errors import ResourceError, ConfigurationError, AgentError

class AgentResource(BaseResource):
    """Resource for accessing other agents."""
    
    def __init__(self, name: str, agent_registry: Dict[str, Any]):
        """Initialize agent resource.
        
        Args:
            name: Resource identifier
            agent_registry: Dictionary mapping agent IDs to agent instances
        """
        super().__init__(name)
        if not agent_registry:
            raise ConfigurationError("Agent registry cannot be empty")
        self.agent_registry = agent_registry

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query an agent from the registry.
        
        Args:
            request: Query parameters including agent_id and query
            
        Returns:
            Response from the agent
            
        Raises:
            ResourceError: If agent query fails
            ConfigurationError: If agent_id is invalid
            AgentError: If agent execution fails
        """
        agent_id = request.get("agent_id")
        if not agent_id:
            raise ConfigurationError("agent_id is required")
            
        agent = self.agent_registry.get(agent_id)
        if not agent:
            raise ConfigurationError(f"Agent not found: {agent_id}")
        
        try:    
            response = await agent.run(request.get("query", {}))
            return {"response": response, "success": True}
        except AgentError as e:
            raise ResourceError(f"Agent {agent_id} execution failed") from e
        except (ValueError, KeyError) as e:
            raise ConfigurationError(f"Invalid query format for agent {agent_id}") from e

    async def initialize(self) -> None:
        """Initialize all agents in registry.
        
        Raises:
            ResourceError: If initialization fails
            AgentError: If agent initialization fails
        """
        for agent_id, agent in self.agent_registry.items():
            try:
                await agent.initialize()
            except (AgentError, ValueError) as e:
                raise ResourceError(f"Failed to initialize agent {agent_id}") from e

    async def cleanup(self) -> None:
        """Clean up all agents in registry concurrently."""
        cleanup_tasks = []
        for agent_id, agent in self.agent_registry.items():
            task = asyncio.create_task(self._cleanup_agent(agent_id, agent))
            cleanup_tasks.append(task)
        
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        errors = [str(e) for e in results if isinstance(e, Exception)]
        
        if errors:
            raise ResourceError("\n".join(errors))

    async def _cleanup_agent(self, agent_id: str, agent: Any) -> None:
        try:
            await agent.cleanup()
        except (AgentError, ValueError) as e:
            raise ResourceError(f"Failed to cleanup agent {agent_id}: {str(e)}") from e