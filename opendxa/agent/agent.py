"""Agent implementation with progressive configuration.

The Agent system follows a Declarative-Imperative pattern:

1. Agent (Declarative Layer)
   - Describes WHAT the agent is and can do
   - Defines capabilities and resources
   - Specifies configuration and identity
   - Focuses on the agent's nature and potential

2. AgentRuntime (Imperative Layer)
   - Defines HOW the agent executes and manages state
   - Controls execution flow and coordination
   - Manages runtime behavior and state
   - Focuses on the agent's operation and execution

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
from opendxa.dana.runtime.runtime_context import RuntimeContext
from opendxa.dana.state import AgentState
from opendxa.agent.agent_runtime import AgentRuntime
from opendxa.common.capability import BaseCapability
from opendxa.common.resource import BaseResource, LLMResource
from opendxa.common.io import BaseIO, IOFactory
from opendxa.common.utils.misc import Misc
from opendxa.common.capability.capable import Capable
from opendxa.config.agent_config import AgentConfig
from opendxa.common.types import BaseResponse
from opendxa.common.mixins.tool_callable import ToolCallable
from opendxa.common.types import BaseRequest

class AgentResponse(BaseResponse):
    """Response from an agent operation."""

    @classmethod
    def new_instance(cls, response: Union[BaseResponse, Dict[str, Any], Any]) -> 'AgentResponse':
        """Create a new AgentResponse instance from a BaseResponse or similar structure.

        Args:
            response: The response to convert, which should have success, content, and error attributes

        Returns:
            AgentResponse instance
        """
        if isinstance(response, BaseResponse):
            return AgentResponse(
                success=response.success,
                content=response.content,
                error=response.error
            )
        elif isinstance(response, ExecutionSignal):
            return AgentResponse(
                success=False if response.type == ExecutionSignalType.CONTROL_ERROR else True,
                content=response.content,
                error=response.content.get("error", None)
            )
        else:
            return AgentResponse(
                success=True,
                content=response,
                error=None
            )


# pylint: disable=too-many-public-methods
class Agent(BaseResource, Capable):
    """Main agent interface with built-in execution management."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """Initialize agent with optional name and description."""
        super().__init__(name=name, description=description)
        self._llm = None
        self._resources = {}
        self._capabilities = {}
        self._io = None
        self._state = None
        self._runtime = None
        self._config = AgentConfig()
        self._initialized = False
        self._resource_registry = {}

    # ===== Core Properties =====
    @property
    def state(self) -> AgentState:
        """Property to get or initialize agent state."""
        if not self._state:
            self._state = AgentState()
        return self._state

    @property
    def runtime(self) -> AgentRuntime:
        """Property to get or initialize agent runtime."""
        if not self._runtime:
            raise ValueError("Agent runtime not initialized")
        return self._runtime

    @property
    def agent_llm(self) -> LLMResource:
        """Property to get or initialize agent LLM."""
        if not self._llm:
            self._llm = self._get_default_llm_resource()
        return self._llm

    @property
    def available_resources(self) -> Dict[str, BaseResource]:
        """Property to get or initialize available resources."""
        if not self._resources:
            self._resources = {}
        return self._resources

    @property
    def capabilities(self) -> Dict[str, BaseCapability]:
        """Property to get or initialize capabilities."""
        if not self._capabilities:
            self._capabilities = {}
        return self._capabilities

    @property
    def io(self) -> BaseIO:
        """Property to get or initialize IO system."""
        if not self._io:
            self._io = IOFactory.create_io()
        return self._io

    # ===== Configuration Methods =====
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

    def with_planning(
        self, 
        strategy: Optional[PlanStrategy] = None, 
        planner: Optional[Planner] = None,
        llm: Optional[Union[Dict, str, LLMResource]] = None
    ) -> 'Agent':
        """Configure planning strategy and LLM.
        
        Args:
            strategy: Planning strategy to use
            planner: Optional planner instance to use
            llm: Optional LLM configuration (dict, string, or LLMResource)
        """
        self.runtime.with_planning(strategy, planner, llm)
        return self

    def with_reasoning(
        self, 
        strategy: Optional[ReasoningStrategy] = None, 
        reasoner: Optional[Reasoner] = None,
        llm: Optional[Union[Dict, str, LLMResource]] = None
    ) -> 'Agent':
        """Configure reasoning strategy and executor.
        
        Args:
            strategy: Reasoning strategy to use
            reasoner: Optional reasoner instance to use
            llm: Optional LLM configuration (dict, string, or LLMResource)
        """
        self.runtime.with_reasoning(strategy, reasoner, llm)
        return self

    # ===== Helper Methods =====
    def _get_default_llm_resource(self):
        """Get default LLM resource."""
        return LLMResource(
            name=f"{self.name}_llm",
            config={"model": self._config.get("model")}
        )

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

    # ===== Lifecycle Methods =====
    def _initialize(self) -> 'Agent':
        """Initialize agent components. Must be called at run-time."""
        if self._initialized:
            return self

        if not self._llm:
            self._llm = self._get_default_llm_resource()
        if not self._state:
            self._state = AgentState()
        if not self._runtime:
            self._runtime = AgentRuntime(agent=self)

        self._initialized = True
        return self

    async def cleanup(self) -> None:
        """Cleanup agent and its components."""
        if self._runtime:
            await self._runtime.cleanup()
            self._runtime: Optional[AgentRuntime] = None

    async def initialize(self) -> 'Agent':
        """Public initialization method."""
        return self._initialize()

    async def __aenter__(self) -> 'Agent':
        """Initialize agent when entering context."""
        self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup agent when exiting context."""
        await self.cleanup()

    # ===== Execution Methods =====
    async def async_run(self, plan: Plan, context: Optional[RuntimeContext] = None) -> AgentResponse:
        """Execute an objective."""
        self._initialize()
        async with self:  # For cleanup
            return AgentResponse.new_instance(await self.runtime.execute(plan, context))

    def run(self, plan: Plan) -> AgentResponse:
        """Run an plan."""
        return Misc.safe_asyncio_run(self.async_run, plan)

    def ask(self, question: str) -> AgentResponse:
        """Ask a question to the agent."""
        plan = PlanFactory.create_basic_plan(question, ["query"])
        return self.run(plan)

    def runtime_context(self) -> RuntimeContext:
        """Get the runtime context."""
        return self.runtime.runtime_context

    @ToolCallable.tool
    def set_variable(self, name: str, value: Any) -> BaseResponse:
        """Set a variable in the RuntimeContext."""
        self.runtime.runtime_context.set_variable(name, value)
        return BaseResponse(success=True, content=f"Variable {name} set to {value}")

    async def query(self, request: BaseRequest) -> BaseResponse:
        """Query the agent."""
        return self.runtime.runtime_context.query(request)
