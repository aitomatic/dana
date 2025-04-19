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
from opendxa.common.config_manager import load_agent_config
from opendxa.common.utils.misc import safe_asyncio_run

@dataclass
class AgentResponse:
    """Response from an agent operation.
    
    This class can handle converting from various data structures into a standardized
    agent response format.
    """
    success: bool
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @classmethod
    def new_instance(cls, response: Union[ResourceResponse, Dict[str, Any], Any]) -> 'AgentResponse':
        """Create a new AgentResponse instance from a ResourceResponse or similar structure.
        
        Args:
            response: The response to convert, which should have success, content, and error attributes
            
        Returns:
            AgentResponse instance
        """
        if isinstance(response, ResourceResponse):
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
class Agent(Configurable, Loggable):
    """Main agent interface with built-in execution management."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        Configurable.__init__(self)

        self._name = name or "agent"
        self._description = description or "Agent responsible for executing tasks and " \
                                           "coordinating activities based on available information"
        self._state = AgentState()
        self._agent_llm = None  # Default LLM
        self._workflow_llm = None  # Specialized LLMs
        self._planning_llm = None
        self._reasoning_llm = None
        # self._planner = None
        # self._reasoner = None
        self._capabilities = None
        self._available_resources = None
        self._io = None
        self._runtime: Optional[AgentRuntime] = None
        self._planning_strategy = PlanStrategy.DEFAULT
        self._reasoning_strategy = ReasoningStrategy.DEFAULT

        Loggable.__init__(self)

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
        if not self._agent_llm:
            self._agent_llm = self._get_default_llm_resource()
        return self._agent_llm
    
    def _get_default_llm_resource(self):
        """Get default LLM resource."""
        return LLMResource(
            name=f"{self._name}_llm",
            config=(
                {"model": self.config["model"]} if "model" in self.config else {}
            )
        )

    @property
    def available_resources(self) -> Dict[str, BaseResource]:
        """Get available resources. Resources are things I can access as needed."""
        if not self._available_resources:
            self._available_resources = {}
        return self._available_resources

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
    
    @property
    def description(self) -> str:
        """Get agent description."""
        return self._description

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._name

    def with_model(self, model: str) -> "Agent":
        """Configure agent model string name"""
        self.config["model"] = model
        return self

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

    def with_resources(self, resources: Dict[str, BaseResource]) -> "Agent":
        """Add resources to agent."""
        if not self._available_resources:
            self._available_resources = {}
        self._available_resources.update(resources)
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

    def with_planning(self, strategy: PlanStrategy) -> 'Agent':
        """Configure planning strategy."""
        self._planning_strategy = strategy
        return self

    def with_reasoning(self, strategy: ReasoningStrategy) -> 'Agent':
        """Configure reasoning strategy."""
        self._reasoning_strategy = strategy
        return self

    def with_planning_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure planning LLM."""
        self._planning_llm = self._create_llm(llm, "planning_llm")
        return self

    def with_reasoning_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure reasoning LLM."""
        self._reasoning_llm = self._create_llm(llm, "reasoning_llm")
        return self

    # def with_mcp(self, config: Dict[str, Any]) -> 'Agent':
    #     """Add MCP resource to agent."""
    #     return self.with_resources({
    #         "mcp": MCPResource(
    #             name="mcp_gateway",
    #             endpoint=config["endpoint"],
    #             context_config=config.get("context")
    #         )
    #     })

    # def with_wot(self, config: Dict[str, Any]) -> 'Agent':
    #     """Add WoT resource to agent."""
    #     return self.with_resources({
    #         "wot": WoTResource(
    #             name="wot_gateway",
    #             directory_endpoint=config["directory"],
    #             thing_description=config.get("thing_description")
    #         )
    #     })

    def _create_llm(self, llm: Union[Dict, str, LLMResource], name: str) -> LLMResource:
        """Create LLM from various input types."""
        if isinstance(llm, LLMResource):
            return llm
        if isinstance(llm, str):
            config = load_agent_config("llm")
            config["model"] = llm
            return LLMResource(name=f"{self._name}_{name}", config=config)
        if isinstance(llm, Dict):
            config = load_agent_config("llm")
            config.update(llm)
            return LLMResource(name=f"{self._name}_{name}", config=config)
        raise ValueError(f"Invalid LLM configuration: {llm}")

    def _initialize(self) -> 'Agent':
        """Internal initialization of agent configuration and runtime.

        This method is idempotent - safe to call multiple times.
        Only initializes if not already initialized.
        """
        if self._runtime:
            return self  # Already initialized

        # Validate minimal config
        if not self._agent_llm:
            self.with_llm(self._get_default_llm_resource())

        # Set default strategies if not specified
        self._planning_strategy = self._planning_strategy or PlanStrategy.DEFAULT
        self._reasoning_strategy = self._reasoning_strategy or ReasoningStrategy.DEFAULT

        # Create runtime with strategies
        self._runtime = AgentRuntime(self)

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
        return safe_asyncio_run(self.async_run, plan)

    def ask(self, question: str) -> AgentResponse:
        """Ask a question to the agent."""
        plan = PlanFactory.create_basic_plan(question, ["query"])
        return self.run(plan)
