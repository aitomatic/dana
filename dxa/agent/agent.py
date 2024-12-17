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
from contextlib import asynccontextmanager

from dxa.agent.agent_state import AgentState
from dxa.core.reasoning import BaseReasoning, ReasoningFactory
from dxa.core.resource import BaseResource
from dxa.core.capability import BaseCapability

class Agent:
    """Main agent interface with built-in execution management."""
    
    def __init__(self, 
                 name: str,
                 reasoning: Optional[Union[str, BaseReasoning]] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.name = name
        self._state = AgentState()
        self._reasoning = None if reasoning is None else ReasoningFactory.create(reasoning)
        self._resources: Dict[str, BaseResource] = {}
        self._capabilities: List[BaseCapability] = []
        self._config = config or {}

    @property
    def state(self) -> AgentState:
        """Get agent state."""
        return self._state

    @property
    def reasoning(self) -> BaseReasoning:
        """Get reasoning system."""
        return self._reasoning
    
    @property
    def resources(self) -> Dict[str, BaseResource]:
        """Get resources."""
        return self._resources
    
    @property
    def capabilities(self) -> List[BaseCapability]:
        """Get capabilities."""
        return self._capabilities
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get configuration."""
        return self._config

    @asynccontextmanager
    async def _execution_context(self):
        """Manage execution context and cleanup."""
        try:
            await self._initialize_resources()
            yield self._state
        finally:
            await self._cleanup_resources()

    async def run(self, task: Union[str, Dict]) -> Any:
        """Execute a task using configured reasoning and resources."""
        if not self._reasoning:
            raise ValueError("Reasoning system not configured")

        async with self._execution_context() as ctx:
            return await self._reasoning.reason_about(task, ctx)

    def with_reasoning(self, reasoning: Union[str, BaseReasoning]) -> "Agent":
        """Configure reasoning system."""
        self._reasoning = ReasoningFactory.create(reasoning)
        return self

    def with_resources(self, resources: Dict[str, BaseResource]) -> "Agent":
        """Add resources to agent."""
        self._resources.update(resources)
        return self

    def with_capabilities(self, capabilities: List[Union[str, BaseCapability]]) -> "Agent":
        """Add capabilities to agent."""
        self._capabilities.extend(capabilities)
        return self

    async def _initialize_resources(self):
        """Initialize all resources."""
        for resource in self._resources.values():
            await resource.initialize()

    async def _cleanup_resources(self):
        """Cleanup all resources."""
        for resource in self._resources.values():
            await resource.cleanup()

    async def __aenter__(self) -> "Agent":
        """Initialize agent resources."""
        await self._initialize_resources()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup agent resources."""
        await self._cleanup_resources()