"""Interactive console-based agent implementation.

This module provides an agent implementation that interacts through the console,
enabling direct user interaction and feedback. It supports both autonomous operation
and interactive dialogue.

Example:
    ```python
    from dxa.agents.interactive import InteractiveAgent
    from dxa.agents.config import AgentConfig, LLMConfig
    from dxa.core.reasoning import ChainOfThoughtReasoning
    
    config = AgentConfig(
        name="math_tutor",
        llm_config=LLMConfig(
            model_name="gpt-4",
            temperature=0.7
        )
    )
    
    agent = InteractiveAgent(
        config=config,
        reasoning=ChainOfThoughtReasoning()
    )
    
    result = await agent.run({
        "task": "solve_equation",
        "equation": "2x + 5 = 13"
    })
    ```
"""

from typing import Optional, Dict, Any
from dxa.agents.base_agent import BaseAgent
from dxa.core.io.base_io import BaseIO
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.agents.config import AgentConfig
from dxa.common.errors import ReasoningError, ConfigurationError, DXAConnectionError

class InteractiveAgent(BaseAgent):
    """Agent that interacts through console I/O.
    
    This agent type provides interactive capabilities through console input/output.
    It can engage in dialogue with users, request clarification, and provide
    step-by-step explanations of its reasoning.
    
    Attributes:
        reasoning: Reasoning system instance
        io: I/O interface for user interaction
        
    Args:
        config: Agent configuration
        reasoning: Reasoning system instance
        io: Optional custom I/O interface (defaults to ConsoleIO)
        
    Example:
        ```python
        agent = InteractiveAgent(
            config=AgentConfig(...),
            reasoning=ChainOfThoughtReasoning(),
            io=CustomIO()  # Optional custom I/O
        )
        ```
    """
    
    def __init__(
        self,
        config: AgentConfig,
        reasoning: BaseReasoning,
        io: Optional[BaseIO] = None
    ):
        """Initialize interactive agent."""
        super().__init__(
            name=config.name,
            config=config.llm_config.__dict__,
            mode="interactive"
        )
        self.reasoning = reasoning
        self.io = io or ConsoleIO()

    async def run(self, task: str) -> Dict[str, Any]:
        """Run the interactive agent's main loop.
        
        This method manages the agent's interaction cycle, including getting user
        input, applying reasoning, and providing responses.
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing:
                - success: Whether the task completed successfully
                - results: Results from reasoning system
                - context: Interaction context and history
                
        Raises:
            ReasoningError: If reasoning system fails
            ConfigurationError: If agent is misconfigured
            DXAConnectionError: If I/O operations fail
            ValueError: If task is invalid
            
        Example:
            ```python
            result = await agent.run({
                "task": "explain_concept",
                "concept": "neural networks",
                "style": "beginner"
            })
            ```
        """
        context = {"task": task}
        try:
            # Get initial input if needed
            if 'initial_input' not in context:
                response = await self.io.get_input(
                    "How can I help you today?"
                )
                context['initial_input'] = response

            # Run reasoning cycle
            result = await self.reasoning.reason(context, task)
            
            # Check if we need user input
            if result.get("needs_user_input"):
                response = await self.io.get_input(result["user_prompt"])
                context['user_input'] = response
            
            return {
                "success": True,
                "results": result,
                "context": context
            }
            
        except (ReasoningError, ConfigurationError, ValueError, DXAConnectionError) as e:
            self.logger.error("Interactive agent error: %s", str(e))
            return {
                "success": False,
                "error": str(e)
            }
