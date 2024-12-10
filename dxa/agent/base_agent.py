"""Base implementation for DXA agents.

This module provides the foundational BaseAgent class that all other agent types
inherit from. It implements core functionality like initialization, resource
management, and error handling.

Class Hierarchy:
    The DXA agent system follows this inheritance structure:
    
    BaseAgent
    ├── AutonomousAgent
    ├── InteractiveAgent       # Specialized for user interaction
    ├── WebSocketAgent        # Specialized for network communication
    ├── WorkAutomationAgent   # Specialized for workflow automation
    └── CollaborativeAgent    # Specialized for multi-agent coordination
    
    Each specialized agent type extends BaseAgent with specific capabilities:
    - AutonomousAgent: Adds independent operation capabilities
    - InteractiveAgent: Adds user interaction capabilities
    - WebSocketAgent: Adds network communication
    - WorkAutomationAgent: Adds workflow management (uses OODA reasoning)
    - CollaborativeAgent: Adds agent coordination capabilities

The base agent provides a default Chain of Thought reasoning system which can be
overridden by specialized agents or client code. For example:
    ```python
    # Use default Chain of Thought reasoning
    agent = MyAgent(name="agent1", config={...})
    
    # Override with custom reasoning
    agent = MyAgent(
        name="agent2", 
        config={...},
        reasoning=CustomReasoning()
    )
    ```

Classes:
    BaseAgent: Abstract base class for all DXA agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator, Optional
from dataclasses import dataclass
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.reasoning.cot_reasoning import ChainOfThoughtReasoning
from dxa.core.resource.expert_resource import ExpertResource
from dxa.agent.agent_llm import AgentLLM
from dxa.agent.agent_progress import AgentProgress
from dxa.common.utils.logging import DXALogger
from dxa.agent.agent_runtime import AgentRuntime
from dxa.agent.agent_state import StateManager
from dxa.core.config import LLMConfig

@dataclass
class AgentConfig:
    """Configuration for DXA agents."""
    name: str
    llm_config: LLMConfig
    reasoning_config: Optional[Dict[str, Any]] = None
    resources_config: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """Base class providing common agent functionality."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        mode: str = "autonomous",
        max_iterations: Optional[int] = None
    ):
        """Initialize base agent.
        
        Args:
            name: Name of this agent
            config: Configuration dictionary
            reasoning: Optional reasoning system (defaults to ChainOfThoughtReasoning)
            mode: Operating mode (default: autonomous)
            max_iterations: Optional maximum iterations
        """
        self.name = name
        self.mode = mode
        
        # Define agent-specific prompts
        agent_prompts = {
            "system_prompt": self.get_agent_system_prompt(),
            "user_prompt": self.get_agent_user_prompt()
        }
        
        # Create our LLM with agent prompts
        self._llm = AgentLLM(
            name=f"{name}_llm", 
            config=config,
            agent_prompts=agent_prompts
        )
        
        # Set up reasoning with our LLM
        self._reasoning = reasoning if reasoning is not None else ChainOfThoughtReasoning()
        self._reasoning.agent_llm = self._llm

        # Initialize resources
        self.resources: Dict[str, Any] = {}
        
        # Set up logging
        log_config = config.get("logging", {})
        self.logger = DXALogger(
            log_dir=log_config.get("dir", "logs"),
            log_level=log_config.get("level", "INFO"),
            max_history=log_config.get("max_history", 1000),
            json_format=log_config.get("json_format", False),
            console_output=log_config.get("console_output", True)
        )
        
        # Set up runtime
        self.runtime = AgentRuntime(
            state_manager=StateManager(name),
            max_iterations=max_iterations
        )

    @property
    def reasoning(self) -> BaseReasoning:
        """Get the reasoning system."""
        return self._reasoning

    async def initialize(self) -> None:
        """Initialize agent and resources."""
        # Initialize our LLM first
        await self._llm.initialize()
        
        # Initialize reasoning (it already has our LLM)
        await self._reasoning.initialize()
        
        # Initialize resources
        for resource in self.resources.values():
            if callable(getattr(resource, "initialize", None)):
                await resource.initialize()
            
        self.logger.log_completion(
            llm_name=self._llm.name,
            llm_model=self._llm.model,
            prompt=f"Initializing agent {self.name}",
            response="Agent initialized with resources: " + ", ".join(self.resources.keys()),
            tokens=0,
            success=True
        )

    async def cleanup(self) -> None:
        """Clean up agent and resources."""
        for resource in self.resources.values():
            if callable(getattr(resource, "cleanup", None)):
                await resource.cleanup()
        
        await self._reasoning.cleanup()
        await self._llm.cleanup()
        
        self.logger.log_completion(
            llm_name=self._llm.name,
            llm_model=self._llm.model,
            prompt=f"Cleaning up agent {self.name}",
            response="Agent cleaned up",
            tokens=0,
            success=True
        )

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent with standardized runtime management.
        
        Args:
            task: Task configuration dictionary containing:
                - objective: Main task objective
                - parameters: Task-specific parameters
                - constraints: Optional execution constraints
                
        Returns:
            Dict containing:
                - success: Whether execution completed successfully
                - iterations: Number of iterations performed
                - results: Results from final reasoning cycle
                - state_history: Record of observations and messages
                - error: Error information if execution failed
        """
        return await self.runtime.execute(
            task=task,
            reasoning_step=self._reasoning_step,
            pre_execute=self._pre_execute,
            post_execute=self._post_execute,
            should_continue=self._should_continue
        )
        
    async def _reasoning_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one reasoning iteration.
        
        Args:
            context: Current execution context
            
        Returns:
            Dict containing reasoning results and any updates to context
        """
        return await self.reasoning.reason(context)
        
    async def _pre_execute(self, context: Dict[str, Any]) -> None:
        """Hook for pre-execution setup.
        
        Args:
            context: Initial execution context to prepare
            
        Returns:
            None
        """
        pass
        
    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Hook for post-execution processing.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results dictionary
        """
        return result
        
    # pylint: disable=unused-argument
    async def _should_continue(self, result: Dict[str, Any]) -> bool:
        """Hook for custom continuation logic.
        
        Args:
            result: Results from last reasoning iteration containing:
                - task_complete: Optional flag indicating task completion
                - is_stuck: Optional flag indicating if reasoning is stuck
                - Any other reasoning-specific results
            
        Returns:
            True if execution should continue, False to stop
            
        Note:
            Base implementation always returns True. Specialized agents can
            override this to implement custom continuation logic based on
            the reasoning results.
        """
        # Base implementation ignores result and always continues
        # Specialized agents can override this to check result contents
        return True

    async def use_expert(self, domain: str, request: str) -> str:
        """Use expert for specialized domain knowledge.
        
        Finds and queries an expert resource for domain-specific knowledge.
        
        Args:
            domain: Domain of expertise required (e.g., "mathematics", "physics")
            request: Query/request for the expert
            
        Returns:
            Expert's response as string
            
        Raises:
            ValueError: If no expert is found for the specified domain
        """
        experts = {
            name: resource for name, resource in self.resources.items()
            if isinstance(resource, ExpertResource)
        }
        
        expert = next(
            (e for e in experts.values() if e.expertise.name.lower() == domain.lower()),
            None
        )
        
        if not expert:
            self.logger.log_error(
                error_type="expert_not_found",
                message=f"No expert found for domain: {domain}"
            )
            raise ValueError(f"No expert found for domain: {domain}")
            
        response = await expert.query({"prompt": request})
        return response["response"]

    async def handle_error(self, error: Exception) -> None:
        """Handle errors during agent execution."""
        self.logger.log_error(
            error_type=error.__class__.__name__,
            message=f"Agent error: {str(error)}"
        )

    async def run_with_progress(self, task: Dict[str, Any]) -> AsyncIterator[AgentProgress]:
        """Run a task with progress updates.
        
        Args:
            task: Task configuration dictionary containing:
                - objective: Main task objective
                - parameters: Task-specific parameters
                - constraints: Optional execution constraints
                
        Yields:
            AgentProgress objects containing:
                - Progress updates during execution (type="progress")
                - Final results or error information (type="result")
                
        Progress Reporting:
            - 0%: Starting execution
            - 10%: After pre-execution
            - 10-90%: During main execution loop
            - 100%: Final result or error
        """
        async for progress in self.runtime.execute_with_progress(
            task=task,
            reasoning_step=self._reasoning_step,
            pre_execute=self._pre_execute,
            post_execute=self._post_execute,
            should_continue=self._should_continue
        ):
            yield progress

    @abstractmethod
    def get_agent_system_prompt(self) -> str:
        """Get the agent-specific system prompt.
        
        This defines the agent's core behavior and capabilities.
        Subclasses must implement this to define their specific behavior.
        """
        pass

    @abstractmethod
    def get_agent_user_prompt(self) -> str:
        """Get the agent-specific user prompt.
        
        This defines how the agent processes user inputs.
        Subclasses must implement this to define their specific interaction style.
        """
        pass
