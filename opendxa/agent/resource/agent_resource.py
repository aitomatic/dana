"""Resource for managing and interacting with DXA agents.

This resource provides a standardized interface for:
1. Initializing and cleaning up multiple agents
2. Routing queries to specific agents
3. Error handling and response formatting

Example:
    ```python
    # Create researcher agent resource
    researcher = Agent("researcher")
    researcher.with_llm({"model": "gpt-4", "temperature": 0.7})
    researcher_resource = AgentResource(
        name="researcher",
        description="Agent for gathering and analyzing information",
        agent=researcher
    )

    # Query the researcher agent
    response = await researcher_resource.query({
        "request": "Research the latest developments in AI safety",
    })
    ```
"""

import asyncio
from typing import TYPE_CHECKING

from opendxa.common.exceptions import AgentError, ResourceError
from opendxa.base.resource.base_resource import BaseResource, ResourceResponse
from opendxa.common.utils.misc import safe_asyncio_run
from opendxa.common.mixins import ToolCallable
from opendxa.common.mixins.queryable import QueryParams

if TYPE_CHECKING:
    from opendxa.agent.agent import Agent  # Only used for type hints


class AgentResource(BaseResource):
    """Resource for accessing and coordinating agent interactions."""

    def __init__(self, name: str, agent: "Agent", description: str):
        """Initialize agent resource.

        Args:
            name: Resource identifier
            agent: Agent instance
        """
        super().__init__(name, description)
        self.agent = agent
        safe_asyncio_run(self.initialize)

    @classmethod
    async def create(cls, name: str, agent: "Agent", description: str) -> "AgentResource":
        """Create and initialize an agent resource.

        Args:
            name: Resource identifier
            agent: Agent instance
            description: Resource description

        Returns:
            Initialized AgentResource instance
        """
        resource = cls(name, agent, description)
        await resource.initialize()
        return resource

    @ToolCallable.tool
    async def query(self, params: QueryParams = None) -> ResourceResponse:
        """Query an agent from the registry.

        Args:
            request: Query parameters

        Returns:
            Response from the agent

        Raises:
            ResourceError: If agent query fails
            AgentError: If agent execution fails
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.agent.ask, request.get("request", ""))
            return ResourceResponse(success=True, content={"response": response})
        except AgentError as e:
            raise ResourceError("Agent execution failed") from e
        except (ValueError, KeyError) as e:
            return ResourceResponse.error_response(f"Invalid query format: {e}")

    async def initialize(self) -> None:
        """Initialize all agents in registry.

        Raises:
            ResourceError: If initialization fails
            AgentError: If agent initialization fails
        """
        try:
            await self.agent.initialize()
        except (AgentError, ValueError) as e:
            raise ResourceError("Failed to initialize agent") from e

    async def cleanup(self) -> None:
        """Clean up all agents in registry concurrently."""
        try:
            await self.agent.cleanup()
        except (AgentError, ValueError) as e:
            raise ResourceError("Failed to cleanup agent") from e
