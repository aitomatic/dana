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

from typing import Optional, Dict, Union, List, Any
from uuid import uuid4

from dxa.core.reasoning import BaseReasoning, ReasoningLevel
from dxa.core.resource import BaseResource
from dxa.core.io import BaseIO
from dxa.common.errors import ConfigurationError
from dxa.agent.agent_runtime import AgentRuntime, StateManager
from dxa.core.reasoning.direct_reasoning import DirectReasoning
from dxa.core.reasoning.cot_reasoning import ChainOfThoughtReasoning
from dxa.core.reasoning.ooda_reasoning import OODAReasoning
from dxa.core.reasoning.dana_reasoning import DANAReasoning
from dxa.core.reasoning.base_reasoning import ReasoningContext
from dxa.core.resource.llm_resource import LLMResource

class AgentLLM(LLMResource):
    """LLM implementation specialized for agent operations."""
    
    def __init__(self, name: str, config: Dict[str, Any], agent_prompts: Optional[Dict[str, str]] = None):
        super().__init__(name=name, config=config)
        self.agent_prompts = agent_prompts or {}
    
    async def query(self, request: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Query LLM with agent-specific processing."""
        messages = request.get('messages', [])
        combined_messages = []
        
        # Handle system messages
        system_content = []
        if self.agent_prompts.get("system_prompt"):
            system_content.append(self.agent_prompts["system_prompt"])
        system_content.extend(m["content"] for m in messages if m["role"] == "system")
        
        if system_content:
            combined_messages.append({
                "role": "system",
                "content": "\n\n".join(system_content)
            })
        
        # Handle user messages
        user_content = []
        if self.agent_prompts.get("user_prompt"):
            user_content.append(self.agent_prompts["user_prompt"])
        user_content.extend(m["content"] for m in messages if m["role"] == "user")
        
        if user_content:
            combined_messages.append({
                "role": "user",
                "content": "\n\n".join(user_content)
            })
        
        response = await super().query(combined_messages, **kwargs)
        return {"content": response.choices[0].message.content if response.choices else ""}

class Agent:
    """Agent with progressive configuration capabilities.
    
    Attributes:
        name: Agent identifier
        llm: Core language model
        reasoning: Current reasoning strategy
        resources: Available tools/APIs
        capabilities: Declared abilities
        io: Input/output handler
    """
    
    def __init__(self, name: Optional[str] = None, llm: LLMResource = None):
        """Initialize Agent with required LLM.
        
        Args:
            name: Agent identifier
            llm: Core language model for reasoning
        """
        self.name = name or str(uuid4())[:8]
        self._llm_resource = llm or LLMResource(name="gpt4", config={"model_name": "gpt-4"})
        self._model = "gpt-4"
        self._mode = "autonomous"
        self._reasoning = None
        self._resources = {}
        self._capabilities = set()
        self._io = None
        self._state_manager = StateManager(self.name)
        self._runtime = AgentRuntime(self._state_manager)
        
    def with_reasoning(self, reasoning: Union[BaseReasoning, str, ReasoningLevel]) -> "Agent":
        """Set reasoning system.
        
        Args:
            reasoning: Either a BaseReasoning instance, string name, or ReasoningLevel
        """
        if isinstance(reasoning, BaseReasoning):
            self._reasoning = reasoning
        else:
            # Convert string/level to appropriate reasoning instance
            strategies = {
                "direct": DirectReasoning,
                "cot": ChainOfThoughtReasoning,
                "ooda": OODAReasoning,
                "dana": DANAReasoning,
                ReasoningLevel.DIRECT: DirectReasoning,
                ReasoningLevel.COT: ChainOfThoughtReasoning,
                ReasoningLevel.OODA: OODAReasoning
            }
            
            strategy_class = strategies.get(reasoning)
            if not strategy_class:
                raise ConfigurationError(f"Unknown reasoning strategy: {reasoning}")
            
            self._reasoning = strategy_class()
        
        # Set LLM resource on reasoning system
        self._reasoning.agent_llm = self.llm
        
        if self._resources:
            self._reasoning.set_available_resources(self._resources)
        return self
        
    def with_resources(self, resources: Dict[str, BaseResource]) -> "Agent":
        """Add resources."""
        self._resources.update(resources)
        if self._reasoning:
            self._reasoning.set_available_resources(self._resources)
        return self
    
    def with_capabilities(self, capabilities: List[str]) -> "Agent":
        """Add capabilities."""
        self._capabilities.update(capabilities)
        return self

    def with_io(self, io_handler: BaseIO) -> "Agent":
        """Set I/O handler."""
        self._io = io_handler
        return self

    @property
    def llm(self) -> LLMResource:
        """Get the agent's LLM resource."""
        return self._llm_resource

    @llm.setter
    def llm(self, llm: LLMResource):
        """Set the agent's LLM resource."""
        self._llm_resource = llm
        if self._reasoning:
            self._reasoning.agent_llm = llm

    async def pre_execute(self, context: ReasoningContext) -> None:
        """Setup before execution."""
        if not self._reasoning:
            raise ConfigurationError("Agent requires reasoning system")
            
        # Add capabilities to context
        context.workspace["capabilities"] = list(self._capabilities)
        
        # Add resources to context
        context.workspace["available_resources"] = list(self._resources.keys())

    async def post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process after execution."""
        result.update({
            "agent_name": self.name,
            "capabilities": list(self._capabilities)
        })
        return result
        
    async def run(self, task: Union[str, Dict[str, Any]]) -> Any:
        """Execute task and return result."""
        if not self._reasoning:
            raise ConfigurationError("Agent requires reasoning system")
            
        context = ReasoningContext(
            objective=task if isinstance(task, str) else task.get('objective'),
            resources=self._resources,
            workspace={},
            history=[]
        )
        
        result = await self._runtime.execute(
            task,
            reasoning_step=self._reasoning.reason_about,
            pre_execute=self.pre_execute,
            post_execute=self.post_execute,
            context=context
        )
        
        return result

    async def cleanup(self) -> None:
        """Clean up agent resources and connections."""
        if self._reasoning:
            await self._reasoning.cleanup()
        
        for resource in self._resources.values():
            await resource.cleanup()
            
        if self._io:
            await self._io.cleanup()
            
        await self._runtime.cleanup()

    @property
    def reasoning(self) -> Optional[BaseReasoning]:
        """Get the agent's reasoning system."""
        return self._reasoning

    @property
    def resources(self) -> Dict[str, BaseResource]:
        """Get the agent's resources."""
        return self._resources.copy()  # Return a copy to prevent direct modification

    @property
    def capabilities(self) -> set[str]:
        """Get the agent's capabilities."""
        return self._capabilities.copy()  # Return a copy to prevent direct modification