"""Agent resource implementation."""

from typing import Dict, Any
import asyncio
from dxa.core.resources.base import (
    BaseResource,
    ResourceUnavailableError
)

class AgentResource(BaseResource):
    """Resource for interacting with other agents."""
    
    def __init__(
        self,
        name: str,
        agent_registry: Dict[str, Any],
        timeout: float = 60.0  # 1 minute default timeout
    ):
        """Initialize agent resource.
        
        Args:
            name: Name of this resource
            agent_registry: Dict mapping agent IDs to agent instances
            timeout: Timeout in seconds for agent responses
        """
        super().__init__(
            name=name,
            description="Resource for inter-agent communication",
            config={"timeout": timeout}
        )
        self.agent_registry = agent_registry
        self.timeout = timeout

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query another agent.
        
        Args:
            request: The request containing:
                - agent_id: ID of agent to query
                - query: Query to send to agent
                - timeout: Optional timeout override
            **kwargs: Additional arguments
            
        Returns:
            Dict containing agent's response
            
        Raises:
            ResourceUnavailableError: If target agent is not available
            asyncio.TimeoutError: If agent response times out
        """
        await super().query(request)  # Check availability
        
        agent_id = request.get('agent_id')
        if not agent_id:
            raise ValueError("No agent_id provided in request")
            
        if agent_id not in self.agent_registry:
            raise ResourceUnavailableError(f"Unknown agent: {agent_id}")
            
        query = request.get('query')
        if not query:
            raise ValueError("No query provided in request")

        timeout = request.get('timeout', self.timeout)
        
        try:
            # Get target agent
            agent = self.agent_registry[agent_id]
            
            # Query agent with timeout
            response = await asyncio.wait_for(
                agent.handle_query(query),
                timeout=timeout
            )
            
            return {
                "success": True,
                "agent_id": agent_id,
                "response": response
            }
            
        except asyncio.TimeoutError:
            self.logger.error(
                "Query to agent %s timed out after %s seconds",
                agent_id,
                timeout
            )
            raise
        except Exception as e:
            self.logger.error(
                "Error querying agent %s: %s",
                agent_id,
                str(e)
            )
            raise

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this resource can handle the request.
        
        Args:
            request: Request to check
            
        Returns:
            True if request can be handled, False otherwise
        """
        # Check if request has required fields
        if not all(k in request for k in ['agent_id', 'query']):
            return False
            
        # Check if target agent exists
        return request['agent_id'] in self.agent_registry

    async def initialize(self) -> None:
        """Initialize agent resource."""
        if not self.agent_registry:
            raise ResourceUnavailableError("No agents registered")
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up agent resource."""
        self.agent_registry.clear()
        self._is_available = False 