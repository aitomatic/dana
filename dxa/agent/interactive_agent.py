"""Interactive agent implementation.

This module provides an agent implementation that interacts with users during execution.
It extends the autonomous agent with interactive capabilities and user-driven control flow.

The InteractiveAgent allows users to:
- Monitor the agent's reasoning process in real-time
- Provide feedback and guidance during execution
- Control the flow of execution (continue/stop)
- Review intermediate results
- Make decisions at key decision points

Example:
    ```python
    from dxa.agent import InteractiveAgent
    from dxa.core.io import WebSocketIO
    
    # Create agent with custom IO handler
    agent = InteractiveAgent(
        name="math_tutor",
        llm_config={"model": "gpt-4"},
        description="Interactive math tutor agent",
        io_handler=WebSocketIO()
    )
    
    # Run with user interaction
    result = await agent.run("Solve: 2x + 5 = 13")
    ```

The agent supports different IO handlers (Console, WebSocket, etc.) through the
dxa.core.io module, allowing flexibility in how user interaction is implemented.
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.common.errors import (
    ReasoningError, 
    ConfigurationError, 
    AgentError,
    ResourceError,
    DXAConnectionError
)

class InteractiveAgent(BaseAgent):
    """An agent that enables real-time interaction with users during execution.
    
    This agent type extends BaseAgent with interactive capabilities that allow users to:
    - Monitor the reasoning process in real-time
    - Provide feedback and guidance during execution
    - Control execution flow through continue/stop decisions
    - Review intermediate results at each step
    - Make decisions at key decision points
    
    Attributes:
        io: IO handler for user interaction (defaults to ConsoleIO)
        iteration_count: Number of reasoning iterations performed
        _is_running: Internal state tracking execution status
        
    The agent supports different IO handlers (Console, WebSocket, etc.) through the
    dxa.core.io module, allowing flexibility in how user interaction is implemented.
    """

    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None,
        io_handler: Optional[Any] = None
    ):
        """Initialize interactive agent."""
        config = {
            "llm": llm_config,
            "description": description,
            "logging": llm_config.get("logging", {})
        }
        
        # Call parent constructor with reasoning
        super().__init__(
            name=name,
            config=config,
            reasoning=reasoning,
            max_iterations=max_iterations
        )
        
        # Initialize IO handler
        self.io = io_handler or ConsoleIO()

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the interactive agent's main loop.
        
        Args:
            task: Dictionary containing task configuration and parameters
            
        Returns:
            Dict containing:
                - success: Whether execution completed successfully
                - iterations: Number of iterations performed
                - results: Final reasoning results
                - interaction_history: Record of user interactions
        """
        context = task.copy()
        interaction_history = []
        
        try:
            self.iteration_count = 0
            
            while self._is_running:
                # Check iteration limit
                if (self.max_iterations is not None and self.iteration_count >= self.max_iterations):
                    await self.io.output("Reached maximum iterations")
                    break
                
                # Run reasoning cycle
                self.iteration_count += 1
                await self.io.output(
                    f"Starting iteration {self.iteration_count}/"
                    f"{self.max_iterations or '∞'}"
                )
                
                # Get reasoning result
                result = await self.reasoning.reason(context, task)
                
                # Show result to user and get feedback
                await self.io.output(f"Reasoning result: {result}")
                should_continue = await self.io.input(
                    "Continue to next iteration? (y/n): "
                )
                
                if should_continue.lower() != 'y':
                    await self.io.output("Stopping at user request")
                    break
                
                # Update context with results
                context.update(result)
                interaction_history.append({
                    "iteration": self.iteration_count,
                    "result": result,
                    "user_continued": should_continue.lower() == 'y'
                })
                
                # Check if task is complete
                if result.get("task_complete"):
                    await self.io.output("Task completed successfully")
                    break
                
                # Check if we're stuck
                if result.get("is_stuck"):
                    await self.io.output(
                        f"Agent is stuck: {result.get('stuck_reason')}"
                    )
                    break
            
            return {
                "success": True,
                "iterations": self.iteration_count,
                "results": result,
                "interaction_history": interaction_history
            }
            
        except (ReasoningError, ConfigurationError, AgentError, 
                ResourceError, DXAConnectionError) as e:
            await self.handle_error(e)
            return {
                "success": False,
                "iterations": self.iteration_count,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "interaction_history": interaction_history
            }
