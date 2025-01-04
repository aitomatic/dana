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
from ..workflow import WorkflowFactory
from ..capability import BaseCapability
from ..resource import BaseResource, LLMResource
from ..io import BaseIO, IOFactory
from ..state import AgentState
from ..workflow import WorkflowStrategy
from ..planning import PlanningStrategy
from ..reasoning import ReasoningStrategy
from ...common.utils.config import load_agent_config
from .agent_runtime import AgentRuntime

# pylint: disable=too-many-public-methods
class Agent:
    """Main agent interface with built-in execution management."""
    
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name: Optional[str] = None):
        self._name = name or "agent"
        self._state = AgentState()
        self._agent_llm = None  # Default LLM
        self._workflow_llm = None  # Specialized LLMs
        self._planning_llm = None
        self._reasoning_llm = None
        self._config = {}
        self._planner = None
        self._reasoner = None
        self._capabilities = None
        self._resources = None
        self._io = None
        self._runtime: Optional[AgentRuntime] = None
        self._workflow_strategy = None
        self._planning_strategy = None
        self._reasoning_strategy = None
    
    @property
    def workflow_strategy(self) -> WorkflowStrategy:
        """Get workflow strategy."""
        return self._workflow_strategy or WorkflowStrategy.DEFAULT
    
    @property
    def planning_strategy(self) -> PlanningStrategy:
        """Get planning strategy."""
        return self._planning_strategy or PlanningStrategy.DEFAULT
    
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

    @property
    def workflow_llm(self) -> Optional[LLMResource]:
        """Get workflow LLM or fallback to default."""
        return self._workflow_llm or self.agent_llm

    @property 
    def planning_llm(self) -> Optional[LLMResource]:
        """Get planning LLM or fallback to default."""
        return self._planning_llm or self.agent_llm

    @property
    def reasoning_llm(self) -> Optional[LLMResource]:
        """Get reasoning LLM or fallback to default."""
        return self._reasoning_llm or self.agent_llm

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

    def with_workflow(self, strategy: WorkflowStrategy) -> 'Agent':
        """Configure workflow strategy."""
        self._workflow_strategy = strategy
        if strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
            # This requires the plan to be aware of the same strategy.
            self._planning_strategy = PlanningStrategy.WORKFLOW_IS_PLAN
        return self

    def with_planning(self, strategy: PlanningStrategy) -> 'Agent':
        """Configure planning strategy."""
        self._planning_strategy = strategy
        if strategy == PlanningStrategy.WORKFLOW_IS_PLAN:
            # This requires the workflow to be aware of the same strategy.
            self._workflow_strategy = WorkflowStrategy.WORKFLOW_IS_PLAN
        return self

    def with_reasoning(self, strategy: ReasoningStrategy) -> 'Agent':
        """Configure reasoning strategy."""
        self._reasoning_strategy = strategy
        return self

    def with_workflow_llm(self, llm: Union[Dict, str, LLMResource]) -> "Agent":
        """Configure workflow LLM."""
        self._workflow_llm = self._create_llm(llm, "workflow_llm")
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
            self.with_llm(LLMResource(name=f"{self._name}_llm"))
        
        # Set default strategies if not specified
        self._workflow_strategy = self._workflow_strategy or WorkflowStrategy.DEFAULT
        self._planning_strategy = self._planning_strategy or PlanningStrategy.DEFAULT
        self._reasoning_strategy = self._reasoning_strategy or ReasoningStrategy.DEFAULT
        
        # Create runtime with strategies
        self._runtime = AgentRuntime(
            self,
            workflow_strategy=self._workflow_strategy,
            planning_strategy=self._planning_strategy,
            reasoning_strategy=self._reasoning_strategy
        )
        
        return self

    async def cleanup(self) -> None:
        """Cleanup agent and its components."""
        if self._runtime:
            await self._runtime.cleanup()
            self._runtime: Optional[AgentRuntime] = None

    async def __aenter__(self) -> 'Agent':
        """Initialize agent when entering context."""
        self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup agent when exiting context."""
        await self.cleanup()

    async def async_run(self, workflow: Workflow) -> Any:
        """Execute an objective."""
        self._initialize()
        
        async with self:  # For cleanup
            return await self.runtime.execute(workflow)
    
    def run(self, workflow: Workflow) -> Any:
        """Run an objective."""
        return asyncio.run(self.async_run(workflow))

    def ask(self, question: str) -> Any:
        """Ask a question to the agent."""
        workflow = WorkflowFactory.create_minimal_workflow(question)
        return self.run(workflow)
