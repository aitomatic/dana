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

# TODO: deprecate this resource in favor of the Agent itself as a Resource

import asyncio
from typing import TYPE_CHECKING

# First-party imports
from dana.common.exceptions import AgentError, ResourceError
from dana.common.mixins import ToolCallable
from dana.common.resource import BaseResource
from dana.common.types import BaseRequest, BaseResponse
from dana.common.utils.misc import Misc

if TYPE_CHECKING:
    from dana.frameworks.agent.agent import Agent  # Only used for type hints


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
        Misc.safe_asyncio_run(self.initialize)

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
    async def query(self, request: BaseRequest | None = None) -> BaseResponse:
        """Query an agent from the registry.

        Args:
            request: Query request

        Returns:
            Response from the agent

        Raises:
            ResourceError: If agent query fails
            AgentError: If agent execution fails
        """
        try:
            if request is None:
                return BaseResponse.error_response("No request provided")

            request_text = request.arguments.get("request", "") if hasattr(request, "arguments") else str(request)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.agent.ask, request_text)
            return BaseResponse(success=True, content={"response": response})
        except AgentError as e:
            raise ResourceError("Agent execution failed") from e
        except (ValueError, KeyError) as e:
            return BaseResponse.error_response(f"Invalid query format: {e}")

    async def initialize(self) -> None:
        """Initialize all agents in registry.

        Raises:
            ResourceError: If initialization fails
            AgentError: If agent initialization fails
        """
        try:
            await self.agent._initialize()
        except (AgentError, ValueError) as e:
            raise ResourceError("Failed to initialize agent") from e

    async def cleanup(self) -> None:
        """Clean up all agents in registry concurrently."""
        try:
            await self.agent.cleanup()
        except (AgentError, ValueError) as e:
            raise ResourceError("Failed to cleanup agent") from e
