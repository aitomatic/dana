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
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.io.console import ConsoleIO

class InteractiveAgent(BaseAgent):
    """An agent that enables real-time interaction with users during execution.
    
    This agent type extends BaseAgent with interactive capabilities that allow users to:
    - Monitor the reasoning process in real-time
    - Provide feedback and guidance during execution
    - Control execution flow through continue/stop decisions
    - Review intermediate results at each step
    - Make decisions at key decision points
    
    Attributes:
        All attributes inherited from BaseAgent
        io: IO handler for user interaction (defaults to ConsoleIO)
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        reasoning: Optional reasoning system instance
        description: Optional agent description
        max_iterations: Optional maximum iterations
        io_handler: Optional custom IO handler
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
            "description": description
        }
        
        super().__init__(
            name=name,
            config=config,
            reasoning=reasoning,
            mode="interactive",
            max_iterations=max_iterations
        )
        
        # Initialize IO handler
        self.io = io_handler or ConsoleIO()

    async def _pre_execute(self, context: Dict[str, Any]) -> None:
        """Set up interactive session.
        
        Args:
            context: Initial execution context
        """
        await self.io.output(
            f"Starting interactive session for task: {context.get('objective', 'No objective specified')}"
        )
        
        # Get initial user input if needed
        if 'user_input' not in context:
            user_input = await self.io.input("Initial input: ")
            context['user_input'] = user_input

    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process results and get final user feedback.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results with user feedback
        """
        await self.io.output(f"Final result: {result}")
        feedback = await self.io.input("Any final comments? ")
        
        result.update({
            "agent_type": "interactive",
            "execution_mode": self.mode,
            "user_feedback": feedback
        })
        return result

    async def _should_continue(self, result: Dict[str, Any]) -> bool:
        """Check if user wants to continue execution.
        
        Args:
            result: Results from last reasoning iteration
            
        Returns:
            True if user wants to continue, False otherwise
        """
        # Show intermediate results
        await self.io.output(f"Iteration result: {result}")
        
        # Check completion conditions
        if result.get("task_complete"):
            await self.io.output("Task appears to be complete.")
            return False
            
        if result.get("is_stuck"):
            await self.io.output(f"Agent is stuck: {result.get('stuck_reason')}")
            return False
        
        # Get user decision
        response = await self.io.input("Continue to next iteration? (y/n): ")
        return response.lower() == 'y'

    async def _reasoning_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one reasoning iteration with user interaction.
        
        Args:
            context: Current execution context
            
        Returns:
            Dict containing reasoning results and user input
        """
        # Show current context
        await self.io.output(f"Current context: {context}")
        
        # Run reasoning
        result = await self.reasoning.reason(context)
        
        # Get user feedback
        feedback = await self.io.input("Feedback for this step: ")
        result["user_feedback"] = feedback
        
        return result
