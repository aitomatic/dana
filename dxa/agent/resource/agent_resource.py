"""Resource for managing and interacting with DXA agents.

This resource provides a standardized interface for:
1. Initializing and cleaning up multiple agents
2. Routing queries to specific agents
3. Error handling and response formatting

Example:
    ```python
    # Create resource with agents
    agents = {
        "researcher": Agent("researcher").with_reasoning("cot"),
        "analyst": Agent("analyst").with_reasoning("ooda")
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
from typing import Dict, Any, TYPE_CHECKING, List
from ...common.resource import BaseResource
from ...common.exceptions import ResourceError, ConfigurationError, AgentError

if TYPE_CHECKING:
    from ..agent import Agent  # Only used for type hints

class AgentResource(BaseResource):
    """Resource for accessing and coordinating agent interactions."""
    
    def __init__(self, name: str, agents: Dict[str, "Agent"]):
        """Initialize agent resource.
        
        Args:
            name: Resource identifier
            agents: Dictionary mapping agent IDs to agent instances
        """
        super().__init__(name)
        if not agents:
            raise ConfigurationError("Agents dictionary cannot be empty")
        self.agents = agents

    @classmethod
    async def create(cls, name: str, agents: Dict[str, "Agent"]) -> "AgentResource":
        """Create and initialize an agent resource.
        
        Args:
            name: Resource identifier
            agents: Dictionary mapping agent IDs to agent instances
            
        Returns:
            Initialized AgentResource instance
        """
        resource = cls(name, agents)
        await resource.initialize()
        return resource

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
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, agent.ask, request.get("query", {}).get("request", ""))
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

    def list_agents(self) -> Dict[str, str]:
        """List all agents in the registry."""
        return {
            f"{agent_id}": agent.description
            for agent_id, agent in self.agents.items()
        }
    
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

    async def _cleanup_agent(self, agent_id: str, agent: "Agent") -> None:
        try:
            await agent.cleanup()
        except (AgentError, ValueError) as e:
            raise ResourceError(f"Failed to cleanup agent {agent_id}: {str(e)}") from e
        
    async def get_tool_strings(
        self, 
        resource_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Format a resource into OpenAI function specification.
        
        Args:
            resource: Resource instance to format
            **kwargs: Additional keyword arguments
            
        Returns:
            OpenAI function specification list
        """

        tool_strings = []
        agents = self.list_agents()
        for agent_id, agent_description in agents.items():
            tool_strings.extend(await super().get_tool_strings(
                resource_id=resource_id, agent_id=agent_id,
                agent_description=agent_description)
            )

        return tool_strings