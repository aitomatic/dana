"""Resource for managing and interacting with DXA agents.

This resource provides a standardized interface for:
1. Initializing and cleaning up multiple agents
2. Routing queries to specific agents
3. Error handling and response formatting

Example:
    ```python
    # Create resource with agents
    agents = {
        "researcher": ResearchAgent(...),
        "analyst": AnalystAgent(...)
    }
    resource = AgentResource("agent_pool", agents)

    # Query specific agent
    response = await resource.query({
        "agent_id": "researcher",
        "query": {"topic": "AI trends"}
    })
    ```
"""

import asyncio
from typing import Dict, Any
from dxa.agent.base_agent import BaseAgent
from dxa.core.resource.base_resource import BaseResource
from dxa.common.errors import ResourceError, ConfigurationError, AgentError

class AgentResource(BaseResource):
    """Resource for accessing and coordinating agent interactions."""
    
    def __init__(self, name: str, agents: Dict[str, BaseAgent]):
        """Initialize agent resource.
        
        Args:
            name: Resource identifier
            agents: Dictionary mapping agent IDs to agent instances
        """
        super().__init__(name)
        if not agents:
            raise ConfigurationError("Agents dictionary cannot be empty")
        self.agents = agents

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
            
        agent = self.agents.get(agent_id)
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
        for agent_id, agent in self.agents.items():
            try:
                await agent.initialize()
            except (AgentError, ValueError) as e:
                raise ResourceError(f"Failed to initialize agent {agent_id}") from e

    async def cleanup(self) -> None:
        """Clean up all agents in registry concurrently."""
        cleanup_tasks = []
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(self._cleanup_agent(agent_id, agent))
            cleanup_tasks.append(task)
        
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        errors = [str(e) for e in results if isinstance(e, Exception)]
        
        if errors:
            raise ResourceError("\n".join(errors))

    async def _cleanup_agent(self, agent_id: str, agent: BaseAgent) -> None:
        try:
            await agent.cleanup()
        except (AgentError, ValueError) as e:
            raise ResourceError(f"Failed to cleanup agent {agent_id}: {str(e)}") from e