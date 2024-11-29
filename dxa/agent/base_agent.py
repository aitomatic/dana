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

from abc import ABC
from typing import Dict, Any, AsyncIterator, Optional
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.resource.expert import ExpertResource
from dxa.agent.agent_llm import AgentLLM
from dxa.agent.progress import AgentProgress
from dxa.common.utils.logging import DXALogger
from dxa.agent.runtime import AgentRuntime
from dxa.agent.state import StateManager

class BaseAgent(ABC):
    """Base class providing common agent functionality.
    
    This abstract class defines the interface and common functionality that all
    DXA agents must implement. It handles resource initialization, reasoning
    system setup, and provides helper methods for expert consultation.
    
    By default, agents use Chain of Thought reasoning (ChainOfThoughtReasoning).
    This can be overridden by:
    1. Passing a different reasoning system in the constructor
    2. Specialized agent classes providing their own defaults
       (e.g., WorkAutomationAgent uses OODA reasoning by default)
    
    Attributes:
        name: Agent identifier
        mode: Operating mode ("autonomous", "interactive", etc.)
        llm: Internal LLM instance for agent processing
        reasoning: Reasoning system instance (defaults to ChainOfThoughtReasoning)
        resources: Dictionary of available resources
        logger: Logger instance for this agent
        runtime: Runtime manager for agent execution
        
    Args:
        name: Name of this agent
        config: Configuration dictionary
        reasoning: Optional reasoning system (defaults to ChainOfThoughtReasoning)
        mode: Operating mode (default: autonomous)
        max_iterations: Optional maximum iterations (default: None)
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        mode: str = "autonomous",
        max_iterations: Optional[int] = None
    ):
        """Initialize base agent."""
        self.name = name
        self.mode = mode
        self.llm = AgentLLM(name=f"{name}_llm", config=config)
        self.reasoning = reasoning or ChainOfThoughtReasoning()
        self.resources: Dict[str, Any] = {}
        
        # Get logging config from main config, with defaults
        log_config = config.get("logging", {})
        self.logger = DXALogger(
            log_dir=log_config.get("dir", "logs"),
            log_level=log_config.get("level", "INFO"),
            max_history=log_config.get("max_history", 1000),
            json_format=log_config.get("json_format", False),
            console_output=log_config.get("console_output", True)
        )
        
        self.runtime = AgentRuntime(
            state_manager=StateManager(name),
            max_iterations=max_iterations
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

    async def initialize(self) -> None:
        """Initialize agent and resources.
        
        Initializes the LLM, reasoning system, and all registered resources.
        Logs initialization status.
        
        Returns:
            None
        """
        await self.llm.initialize()
        await self.reasoning.initialize()

        for resource in self.resources.values():
            if callable(getattr(resource, "initialize", None)):
                await resource.initialize()
            
        self.logger.log_completion(
            prompt=f"Initializing agent {self.name}",
            response="Agent initialized with resources: " + ", ".join(self.resources.keys()),
            tokens=0,
            success=True
        )

    async def cleanup(self) -> None:
        """Clean up agent and resources.
        
        Cleans up all resources, reasoning system, and LLM.
        Logs cleanup status.
        
        Returns:
            None
        """
        for resource in self.resources.values():
            if callable(getattr(resource, "cleanup", None)):
                await resource.cleanup()
        
        await self.reasoning.cleanup()
        await self.llm.cleanup()
        
        self.logger.log_completion(
            prompt=f"Cleaning up agent {self.name}",
            response="Agent cleaned up",
            tokens=0,
            success=True
        )

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
