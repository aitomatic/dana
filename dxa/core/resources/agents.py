"""Agent resource implementation."""

from typing import Dict, Any
import asyncio
from dxa.core.resources.base_resource import BaseResource, ResourceError
from typing import Optional, List

class AgentError(ResourceError):
    """Error in agent interaction."""
    pass

class AgentResource(BaseResource):
    """Resource for interacting with other agents."""
    
    def __init__(
        self,
        name: str,
        agent_registry: Dict[str, Any],
        timeout: float = 60.0  # 1 minute default timeout
    ):
        """Initialize agent resource."""
        super().__init__(
            name=name,
            description="Resource for inter-agent communication",
            config={"timeout": timeout}
        )
        self.agent_registry = agent_registry
        self.timeout = timeout

    async def initialize(self) -> None:
        """Initialize agent resource."""
        if not self.agent_registry:
            self._is_available = False
            raise AgentError("No agents registered")
        self._is_available = True
        self.logger.info("Agent resource initialized with %d agents", len(self.agent_registry))

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query another agent."""
        agent_id = request.get('agent_id')
        if not agent_id:
            raise ValueError("No agent_id provided in request")
            
        if agent_id not in self.agent_registry:
            raise AgentError(f"Unknown agent: {agent_id}")
            
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
            raise AgentError(f"Query to agent {agent_id} timed out")
        except Exception as e:
            self.logger.error(
                "Error querying agent %s: %s",
                agent_id,
                str(e)
            )
            raise AgentError(f"Query to agent {agent_id} failed: {str(e)}")

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this resource can handle the request."""
        # Check if request has required fields
        if not all(k in request for k in ['agent_id', 'query']):
            return False
            
        # Check if target agent exists
        return request['agent_id'] in self.agent_registry

    async def cleanup(self) -> None:
        """Clean up agent resource."""
        self.agent_registry.clear()
        self._is_available = False
        self.logger.info("Agent resource cleaned up")

    async def broadcast(
        self,
        query: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Broadcast query to all agents."""
        results = {}
        timeout = timeout or self.timeout
        
        try:
            tasks = [
                asyncio.create_task(
                    self.query({
                        "agent_id": agent_id,
                        "query": query,
                        "timeout": timeout
                    })
                )
                for agent_id in self.agent_registry
            ]
            
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
            
            # Collect results
            for task in done:
                try:
                    result = await task
                    results[result["agent_id"]] = result["response"]
                except Exception as e:
                    self.logger.error("Task failed: %s", str(e))
            
            return {
                "success": True,
                "responses": results
            }
            
        except Exception as e:
            self.logger.error("Broadcast failed: %s", str(e))
            raise AgentError(f"Broadcast failed: {str(e)}")

    async def query_with_fallback(
        self,
        primary_agent: str,
        fallback_agents: List[str],
        query: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Query primary agent with fallbacks if it fails."""
        timeout = timeout or self.timeout
        
        try:
            # Try primary agent first
            try:
                result = await self.query({
                    "agent_id": primary_agent,
                    "query": query,
                    "timeout": timeout
                })
                return result
            except AgentError:
                self.logger.warning(
                    "Primary agent %s failed, trying fallbacks",
                    primary_agent
                )
            
            # Try fallback agents
            for agent_id in fallback_agents:
                try:
                    result = await self.query({
                        "agent_id": agent_id,
                        "query": query,
                        "timeout": timeout
                    })
                    return result
                except AgentError:
                    continue
            
            raise AgentError("All agents failed")
            
        except Exception as e:
            self.logger.error("Query with fallback failed: %s", str(e))
            raise AgentError(f"Query with fallback failed: {str(e)}") 