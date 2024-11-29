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
from dxa.core.io.console_io import ConsoleIO

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
        config: Configuration dictionary
        reasoning: Optional reasoning system instance
        description: Optional agent description
        max_iterations: Optional maximum iterations
        io_handler: Optional custom IO handler
    """

    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None,
        io_handler: Optional[Any] = None
    ):
        """Initialize interactive agent.
        
        Args:
            name: Agent identifier
            config: Configuration dictionary
            reasoning: Optional reasoning system instance
            description: Optional agent description
            max_iterations: Optional maximum iterations
            io_handler: Optional custom IO handler
        """
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
        await self.io.send_message(
            f"Starting interactive session for task: {context.get('objective', 'No objective specified')}"
        )
        
        # Get initial user input if needed
        if 'user_input' not in context:
            user_input = await self.io.get_input("Initial input: ")
            context['user_input'] = user_input

    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process results and get final user feedback.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results with user feedback
        """
        await self.io.send_message(f"Final result: {result}")
        feedback = await self.io.get_input("Any final comments? ")
        
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
        await self.io.send_message(f"Iteration result: {result}")
        
        # Check completion conditions
        if result.get("task_complete"):
            await self.io.send_message("Task appears to be complete.")
            return False
            
        if result.get("is_stuck"):
            await self.io.send_message(f"Agent is stuck: {result.get('stuck_reason')}")
            return False
        
        # Get user decision
        response = await self.io.get_input("Continue to next iteration? (y/n): ")
        return response.lower() == 'y'

    async def _reasoning_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one reasoning iteration with user interaction.
        
        Args:
            context: Current execution context
            
        Returns:
            Dict containing reasoning results and user input
        """
        # Show current context
        await self.io.send_message(f"Current context: {context}")
        
        # Extract query from context or use objective as fallback
        query = context.get("query") or context.get("objective", "")
        
        # Run reasoning with both context and query
        step_result = await self.reasoning.reason(context, query)
        
        # Get user feedback
        feedback = await self.io.get_input("Feedback for this step: ")
        
        # Convert StepResult to dict and add feedback
        result_dict = {
            "status": step_result.status,
            "content": step_result.content,
            "next_step": step_result.next_step,
            "resource_request": step_result.resource_request,
            "final_answer": step_result.final_answer,
            "error_message": step_result.error_message,
            "user_feedback": feedback
        }
        
        return result_dict

    def get_agent_system_prompt(self) -> str:
        return """You are an interactive agent that works collaboratively with users.
        You should:
        - Explain your thinking clearly
        - Ask for clarification when needed
        - Provide step-by-step explanations
        - Confirm important decisions with the user
        """

    def get_agent_user_prompt(self) -> str:
        return """Let's work through this together. I'll explain my thinking and
        ask for your input when needed."""
