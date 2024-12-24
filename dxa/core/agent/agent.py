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
        .with_capabilities({"research": ResearchCapability()})
    
    result = await agent.run("Research quantum computing")
    ```

See dxa/agent/README.md for detailed design documentation.
"""

import asyncio
from typing import Dict, Union, Optional, Any
from ..workflow import Workflow
from ..types import Objective
from ..planning import BasePlanner, PlannerFactory 
from ..reasoning import BaseReasoner, ReasonerFactory
from ..capability import BaseCapability
from ..resource import BaseResource, LLMResource
from ..io import BaseIO, IOFactory
from ..state import AgentState
from .agent_runtime import AgentRuntime
from ...common.utils import load_agent_config

class Agent:
    """Main agent interface with built-in execution management."""
    
    def __init__(self, name: Optional[str] = None):
        self._name = name or "agent"
        self._state = AgentState()
        self._agent_llm = None
        self._config = {}
        self._planner = None
        self._reasoner = None
        self._capabilities = None
        self._resources = None
        self._io = None
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
    def agent_llm(self) -> LLMResource:
        """Get agent LLM."""
        if not self._agent_llm:
            self._agent_llm = LLMResource(name=f"{self._name}_llm")
        return self._agent_llm
    
    @property
    def planner(self) -> BasePlanner:
        """Get planning system."""
        if not self._planner:
            self._planner = PlannerFactory.create_planner()
        return self._planner

    @property
    def reasoner(self) -> BaseReasoner:
        """Get reasoning system."""
        if not self._reasoner:
            self._reasoner = ReasonerFactory.create_reasoner()
        return self._reasoner
    
    @property
    def resources(self) -> Dict[str, BaseResource]:
        """Get resources."""
        if not self._resources:
            self._resources = {}
        return self._resources
    
    @property
    def capabilities(self) -> Dict[str, BaseCapability]:
        """Get capabilities."""
        if not self._capabilities:
            self._capabilities = {}
        return self._capabilities

    @property
    def io(self) -> BaseIO:
        """Get IO system."""
        if not self._io:
            self._io = IOFactory.create_io()
        return self._io

    def with_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure agent LLM."""
        if isinstance(llm, LLMResource):
            self._agent_llm = llm
        elif isinstance(llm, str):
            config = load_agent_config("llm")
            config["model"] = llm
            self._agent_llm = LLMResource(name=f"{self._name}_llm", config=config)
        elif isinstance(llm, Dict):
            config = load_agent_config("llm")
            config.update(llm)
            self._agent_llm = LLMResource(name=f"{self._name}_llm", config=config)
        return self
    
    def with_planner(self, planner: Union[str, BasePlanner]) -> "Agent":
        """Configure planning system."""
        self._planner = PlannerFactory.create_planner(planner)
        return self

    def with_reasoner(self, reasoner: Union[str, BaseReasoner]) -> "Agent":
        """Configure reasoning system."""
        self._reasoner = ReasonerFactory.create_reasoner(reasoner)
        return self

    def with_resources(self, resources: Dict[str, BaseResource]) -> "Agent":
        """Add resources to agent."""
        if not self._resources:
            self._resources = {}
        self._resources.update(resources)
        return self

    def with_capabilities(self, capabilities: Dict[str, BaseCapability]) -> "Agent":
        """Add capabilities to agent."""
        if not self._capabilities:
            self._capabilities = {}
        self._capabilities.update(capabilities)
        return self
    
    def with_io(self, io: BaseIO) -> "Agent":
        """Set agent IO to provided IO."""
        self._io = io
        return self

    async def initialize(self) -> None:
        """Initialize agent and its components."""
        if not self.planner or not self.reasoner:
            raise ValueError("Agent must have both planning and reasoning configured")
        
        self._runtime = AgentRuntime(agent=self)
        await self._runtime.initialize()

    async def cleanup(self) -> None:
        """Cleanup agent and its components."""
        if self._runtime:
            await self._runtime.cleanup()
            self._runtime = None

    async def __aenter__(self) -> "Agent":
        """Initialize agent when entering context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup agent when exiting context."""
        await self.cleanup()

    async def run(self,
                  objective: Optional[Union[str, Objective]] = None,
                  workflow: Optional[Workflow] = None
                  ) -> Any:
        """Execute an objective."""
        async with self:
            if not self._runtime:
                raise RuntimeError("Agent must be initialized before running")

            if workflow is None:
                workflow = Workflow(objective)

            return await self._runtime.execute(workflow)
    
    def ask(self, question: str) -> str:
        """Ask a question to the agent."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(question))
