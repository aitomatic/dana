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

from typing import Dict, Union, Optional, Any
from dataclasses import dataclass
from opendxa.base.execution import (
    ExecutionContext
)
from opendxa.execution import (
    Plan,
    PlanFactory,
    PlanStrategy,
    ReasoningStrategy,
    AgentRuntime,
    AgentState,
)
from opendxa.base.capability import BaseCapability
from opendxa.base.resource import BaseResource, LLMResource, ResourceResponse
from opendxa.base.state import WorldState, ExecutionState
from opendxa.common.io import BaseIO, IOFactory
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.misc import Misc
from opendxa.base.capability.capable import Capable
from opendxa.common.mixins.queryable import QueryResponse
from opendxa.config.agent_config import AgentConfig
from opendxa.execution.planning import Planner
from opendxa.execution.reasoning import Reasoner
from opendxa.common.mixins.tool_callable import ToolCallable

@dataclass
class AgentResponse(ResourceResponse):
    """Response from an agent operation."""
    
    @classmethod
    def new_instance(cls, response: Union[ResourceResponse, Dict[str, Any], Any]) -> 'AgentResponse':
        """Create a new AgentResponse instance from a ResourceResponse or similar structure.
        
        Args:
            response: The response to convert, which should have success, content, and error attributes
            
        Returns:
            AgentResponse instance
        """
        if isinstance(response, ResourceResponse) or isinstance(response, QueryResponse):
            return AgentResponse(
                success=response.success,
                content=response.content,
                error=response.error
            )
        else:
            return AgentResponse(
                success=True,
                content=response,
                error=None
            )


# pylint: disable=too-many-public-methods
class Agent(Configurable, Capable, ToolCallable):
    """Main agent interface with built-in execution management."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """Initialize agent with optional name and description."""
        super().__init__()
        self.name = name or "agent"
        self.description = description or "An agent that can execute tasks"
        self._llm = None
        self._planning_executor = None
        self._reasoner = None
        self._resources = {}
        self._capabilities = {}
        self._io = None
        self._state = None
        self._runtime = None
        self._planning_llm = None
        self._reasoning_llm = None
        self._workflow_llm = None
        self._reasoning_strategy = ReasoningStrategy.DEFAULT
        self._planning_strategy = PlanStrategy.DEFAULT

        # Initialize configuration
        self._config = AgentConfig()

        Loggable.__init__(self)
        Capable.__init__(self, self._capabilities)
        ToolCallable.__init__(self)

    @property
    def planning_strategy(self) -> PlanStrategy:
        """Get planning strategy."""
        return self._planning_strategy or PlanStrategy.DEFAULT

    @property
    def reasoning_strategy(self) -> ReasoningStrategy:
        """Get reasoning strategy."""
        return self._reasoning_strategy or ReasoningStrategy.DEFAULT

    @property
    def state(self) -> AgentState:
        """Get agent state."""
        return self._state

    @property
    def runtime(self) -> AgentRuntime:
        """Get agent runtime."""
        if not self._runtime:
            raise ValueError("Agent runtime not initialized")
        return self._runtime

    @property
    def agent_llm(self) -> LLMResource:
        """Get agent LLM."""
        if not self._llm:
            self._llm = self._get_default_llm_resource()
        return self._llm
    
    def _get_default_llm_resource(self):
        """Get default LLM resource."""
        return LLMResource(
            name=f"{self.name}_llm",
            config={"model": self._config.get("model")}
        )

    @property
    def available_resources(self) -> Dict[str, BaseResource]:
        """Get available resources. Resources are things I can access as needed."""
        if not self._resources:
            self._resources = {}
        return self._resources

    @property
    def capabilities(self) -> Dict[str, BaseCapability]:
        """Get capabilities. Capabilities are things I can do."""
        if not self._capabilities:
            self._capabilities = {}
        return self._capabilities

    @property
    def io(self) -> BaseIO:
        """Get IO system."""
        if not self._io:
            self._io = IOFactory.create_io()
        return self._io

    @property
    def workflow_llm(self) -> LLMResource:
        """Get workflow LLM or fallback to default."""
        return self._workflow_llm or self.agent_llm

    @property
    def planning_llm(self) -> LLMResource:
        """Get planning LLM or fallback to default."""
        return self._planning_llm or self.agent_llm

    @property
    def reasoning_llm(self) -> LLMResource:
        """Get reasoning LLM or fallback to default."""
        return self._reasoning_llm or self.agent_llm
    
    def with_model(self, model: str) -> "Agent":
        """Configure agent model string name"""
        self._config.update({"model": model})
        return self

    def with_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure agent LLM."""
        if isinstance(llm, LLMResource):
            self._llm = llm
        elif isinstance(llm, str):
            self._llm = LLMResource(
                name=f"{self.name}_llm",
                config={"model": llm}
            )
        elif isinstance(llm, Dict):
            self._llm = LLMResource(
                name=f"{self.name}_llm",
                config=llm
            )
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

    def with_planning(self, strategy: Optional[PlanStrategy] = None, planner: Optional[Planner] = None) -> 'Agent':
        """Configure planning strategy."""
        if strategy:
            self._planning_strategy = strategy
        if planner:
            self._planning_executor = planner
        return self

    def with_reasoning(self, strategy: Optional[ReasoningStrategy] = None, reasoner: Optional[Reasoner] = None) -> 'Agent':
        """Configure reasoning strategy and executor."""
        if strategy:
            self._reasoning_strategy = strategy
        if reasoner:
            self._reasoner = reasoner
        return self

    def with_planning_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure planning LLM."""
        self._planning_llm = self._create_llm(llm, "planning_llm")
        return self

    def with_reasoning_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure reasoning LLM."""
        self._reasoning_llm = self._create_llm(llm, "reasoning_llm")
        return self

    def _create_llm(self, llm: Union[Dict, str, LLMResource], name: str) -> LLMResource:
        """Create LLM from various input types."""
        if isinstance(llm, LLMResource):
            return llm
        if isinstance(llm, str):
            return LLMResource(
                name=f"{self.name}_{name}",
                config={"model": llm}
            )
        if isinstance(llm, Dict):
            return LLMResource(
                name=f"{self.name}_{name}",
                config=llm
            )
        raise ValueError(f"Invalid LLM configuration: {llm}")

    def _initialize(self) -> 'Agent':
        """Initialize agent components."""
        if not self._llm:
            self._llm = self._get_default_llm_resource()
        if not self._planning_executor:
            self._planning_executor = Planner(strategy=self._planning_strategy)
        if not self._reasoner:
            self._reasoner = Reasoner(strategy=self._reasoning_strategy)
        if not self._io:
            self._io = IOFactory.create_io()
        if not self._state:
            self._state = AgentState()
        if not self._runtime:
            self._runtime = AgentRuntime(self, self._planning_executor, self._reasoner)
        return self

    async def cleanup(self) -> None:
        """Cleanup agent and its components."""
        if self._runtime:
            await self._runtime.cleanup()
            self._runtime: Optional[AgentRuntime] = None

    async def initialize(self) -> None:
        """Public initialization method."""
        self._initialize()

    async def __aenter__(self) -> 'Agent':
        """Initialize agent when entering context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup agent when exiting context."""
        await self.cleanup()

    async def async_run(self, plan: Plan, context: Optional[ExecutionContext] = None) -> AgentResponse:
        """Execute an objective."""
        self._initialize()

        # Create new context if none provided
        if context is None:
            context = ExecutionContext(
                agent_state=self.state,
                world_state=WorldState(),
                execution_state=ExecutionState(),
                planning_llm=self.planning_llm,
                reasoning_llm=self.reasoning_llm,
                available_resources=self.available_resources
            )
        else:
            # Update LLMs in provided context if not set
            if not context.planning_llm:
                context.planning_llm = self.planning_llm
            if not context.reasoning_llm:
                context.reasoning_llm = self.reasoning_llm
        
        assert context.planning_llm is not None
        assert context.reasoning_llm is not None

        async with self:  # For cleanup
            return AgentResponse.new_instance(await self.runtime.execute(plan, context))

    def run(self, plan: Plan) -> AgentResponse:
        """Run an plan."""
        return Misc.safe_asyncio_run(self.async_run, plan)

    def ask(self, question: str) -> AgentResponse:
        """Ask a question to the agent."""
        plan = PlanFactory.create_basic_plan(question, ["query"])
        return self.run(plan)
