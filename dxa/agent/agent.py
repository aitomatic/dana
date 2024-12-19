"""Agent implementation with progressive configuration.

Core Components:
    - LLM: Required language model for reasoning
    - Reasoning: Strategy for approaching tasks
    - Resources: Optional tools and capabilities
    - IO: Optional interaction handlers

Example:
    ```python
    agent = Agent("researcher", llm=LLMResource(...))\\
        .with_reasoning("cot")\\
        .with_resources({"search": SearchResource()})\\
        .with_capabilities(["research"])
    
    result = await agent.run("Research quantum computing")
    ```

See dxa/agent/README.md for detailed design documentation.
"""

from typing import Dict, List, Union, Optional, Any
from dxa.agent.agent_state import AgentState
from dxa.agent.agent_runtime import AgentRuntime
from dxa.core.planning import BasePlanning
from dxa.core.reasoning import BaseReasoning
from dxa.core.capability import BaseCapability
from dxa.core.resource import BaseResource
from dxa.core.io import BaseIO
from dxa.agent.agent_factory import AgentFactory

class Agent:
    """Main agent interface with built-in execution management."""
    
    def __init__(self, 
                 name: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 planning: Optional[Union[str, BasePlanning]] = None,
                 reasoning: Optional[Union[str, BaseReasoning]] = None,
                 capabilities: Optional[List[str, BaseCapability]] = None,
                 resources: Optional[List[BaseResource]] = None,
                 io: Optional[BaseIO] = None):
        self._name = name or "agent"
        self._state = AgentState()
        self._config = config or {}
        self._planning = AgentFactory.create_planning(planning)
        self._reasoning = AgentFactory.create_reasoning(reasoning)
        self._capabilities = AgentFactory.create_capabilities(capabilities)
        self._resources = AgentFactory.create_resources(resources)
        self._io = AgentFactory.create_io(io)
        self._runtime = None
    
    @property
    def state(self) -> AgentState:
        """Get agent state."""
        return self._state

    @property
    def config(self) -> Dict[str, Any]:
        """Get configuration."""
        return self._config
    
    @property
    def planning(self) -> BasePlanning:
        """Get planning system."""
        if not self._planning:
            self._planning = AgentFactory.create_planning()
        return self._planning

    @property
    def reasoning(self) -> BaseReasoning:
        """Get reasoning system."""
        if not self._reasoning:
            self._reasoning = AgentFactory.create_reasoning()
        return self._reasoning
    
    @property
    def resources(self) -> Dict[str, BaseResource]:
        """Get resources."""
        if not self._resources:
            self._resources = AgentFactory.create_resources()
        return self._resources
    
    @property
    def capabilities(self) -> List[BaseCapability]:
        """Get capabilities."""
        if not self._capabilities:
            self._capabilities = AgentFactory.create_capabilities()
        return self._capabilities

    @property
    def io(self) -> BaseIO:
        """Get IO system."""
        if not self._io:
            self._io = AgentFactory.create_io()
        return self._io

    def with_planning(self, planning: Union[str, BasePlanning]) -> "Agent":
        """Configure planning system."""
        self._planning = AgentFactory.create_planning(planning)
        return self

    def with_reasoning(self, reasoning: Union[str, BaseReasoning]) -> "Agent":
        """Configure reasoning system."""
        self._reasoning = AgentFactory.create_reasoning(reasoning)
        return self

    def with_resources(self, resources: Dict[str, BaseResource]) -> "Agent":
        """Add resources to agent."""
        self._resources.add(resources)
        return self

    def with_capabilities(self, capabilities: List[Union[str, BaseCapability]]) -> "Agent":
        """Add capabilities to agent."""
        self._capabilities.add(capabilities)
        return self
    
    def with_io(self, io: BaseIO) -> "Agent":
        """Add IO to agent."""
        self._io = io
        return self

    async def __aenter__(self) -> "Agent":
        """Initialize runtime when entering context"""
        if not self.planning or not self.reasoning:
            raise ValueError("Agent must have both planning and reasoning configured")
        
        self._runtime = AgentRuntime(
            planning=self.planning,
            reasoning=self.reasoning,
            resources=self.resources
        )
        await self._runtime.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup runtime when exiting context"""
        if self._runtime:
            await self._runtime.cleanup()

    async def run(self, objective: str, **kwargs) -> Any:
        """
        Execute an objective. Can be used directly or within context manager.
        Creates temporary runtime if not in context.
        """
        if self._runtime is None:
            async with self:
                return await self._runtime.execute(objective, **kwargs)
        return await self._runtime.execute(objective, **kwargs)