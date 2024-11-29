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

TODO:
    - Integrate core capabilities system:
        - Add capability registration/management
        - Implement standard capabilities (memory, expertise)
        - Add capability dependency resolution
    
    - Implement I/O system integration:
        - Add I/O handler registration
        - Support multiple I/O channels
        - Add I/O routing/multiplexing
    
    - Enhance resource management:
        - Add resource discovery
        - Implement resource lifecycle management
        - Add resource access controls
        - Support dynamic resource loading
    
    - Add state management:
        - Implement agent state persistence
        - Add state recovery mechanisms
        - Support state synchronization
    
    - Improve error handling:
        - Add more granular error types
        - Implement recovery strategies
        - Add error reporting system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator, Optional
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.reasoning.cot import ChainOfThoughtReasoning
from dxa.core.resource.expert import ExpertResource
from dxa.agent.agent_llm import AgentLLM
from dxa.agent.progress import AgentProgress
from dxa.common.utils.logging import DXALogger
from dxa.common.errors import (
    ReasoningError, 
    ConfigurationError, 
    AgentError,
    ResourceError,
    DXAConnectionError
)

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
        
    Args:
        name: Name of this agent
        config: Configuration dictionary
        reasoning: Optional reasoning system (defaults to ChainOfThoughtReasoning)
        mode: Operating mode (default: autonomous)
        max_iterations: Optional maximum iterations (default: None)
        
    Example:
        ```python
        # Using default reasoning
        agent = MyAgent(
            name="default_agent",
            config={...}
        )
        
        # Using custom reasoning
        agent = MyAgent(
            name="custom_agent",
            config={...},
            reasoning=CustomReasoning()
        )
        ```
    """
    
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
            max_iterations: Optional maximum iterations (default: None)
        """
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
        
        self._is_running = False
        self.max_iterations = max_iterations
        self.iteration_count = 0

    @abstractmethod
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent.
        
        Args:
            task: Dictionary containing task configuration and parameters
            
        Returns:
            Dict containing results of the agent's execution
        """
        raise NotImplementedError

    async def initialize(self) -> None:
        """Initialize agent and resources."""
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
        """Clean up agent and resources."""
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
            
        Example:
            ```python
            response = await agent.use_expert(
                domain="mathematics",
                request="Solve: 2x + 5 = 13"
            )
            ```
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
            task: Task configuration dictionary
            
        Yields:
            AgentProgress objects containing progress or result information
            
        Raises:
            ReasoningError: If reasoning system fails
            ConfigurationError: If agent is misconfigured
            AgentError: If agent operations fail
            ResourceError: If resource operations fail
            DXAConnectionError: If connections fail
            ValueError: If task parameters are invalid
        """
        try:
            # Initial progress
            yield AgentProgress(
                type="progress",
                message="Starting task",
                percent=0
            )
            
            # Run the task with intermediate updates
            result = await self.run(task)
            
            # Final progress with result
            yield AgentProgress(
                type="result",
                message="Task completed",
                percent=100,
                result=result
            )
            
        except (
            ReasoningError,
            ConfigurationError,
            AgentError,
            ResourceError,
            DXAConnectionError,
            ValueError
        ) as e:
            # Error progress with specific error information
            yield AgentProgress(
                type="result",
                message=f"Task failed: {str(e)}",
                result={
                    "success": False,
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
            )
