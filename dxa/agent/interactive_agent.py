"""Interactive console-based agent implementation.

This module provides an agent that interacts through the console, enabling
direct user interaction and feedback. The agent handles its own input/output
through a console interface and uses a reasoning system to process user requests.

Example:
    ```python
    config = {
        "name": "math_tutor",
        "model": "gpt-4",
        "temperature": 0.7,
        "system_prompt": "You are a helpful math tutor..."
    }
    
    agent = InteractiveAgent(
        config=config,
        reasoning=ChainOfThoughtReasoning()
    )
    
    result = await agent.run()  # Starts interactive session
    ```
"""

from typing import Optional, Dict, Any
from dxa.agent.base_agent import BaseAgent
from dxa.core.io.base_io import BaseIO
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.common.errors import ReasoningError, ConfigurationError, DXAConnectionError

class InteractiveAgent(BaseAgent):
    """Agent that interacts through console I/O.
    
    This agent handles interactive dialogue through console input/output.
    It manages its own interaction flow, prompting the user for input
    and providing responses through the configured I/O interface.
    
    The agent uses a reasoning system to process user input and generate
    appropriate responses. It can maintain context across multiple
    interactions in a session.
    
    Attributes:
        reasoning: System for processing user input and generating responses
        io: Interface for user interaction (defaults to console)
        
    Args:
        config: Dictionary containing:
            - name: Agent identifier
            - model: Name of the LLM model to use
            - temperature: Model temperature setting
            - system_prompt: Instructions for the agent's behavior
            - Additional LLM configuration parameters
        reasoning: System for processing inputs and generating responses
        io: Optional custom I/O interface (defaults to ConsoleIO)
        
    Example:
        ```python
        agent = InteractiveAgent(
            config={
                "name": "helper",
                "model": "gpt-4",
                "system_prompt": "You are a helpful assistant"
            },
            reasoning=ChainOfThoughtReasoning()
        )
        ```
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        reasoning: BaseReasoning,
        io: Optional[BaseIO] = None
    ):
        """Initialize interactive agent."""
        super().__init__(
            name=config["name"],
            config=config,
            mode="interactive"
        )
        self.reasoning = reasoning
        self.io = io or ConsoleIO()

    async def run(self) -> Dict[str, Any]:
        """Start an interactive session with the user.
        
        Manages the interaction loop:
        1. Prompts user for input
        2. Processes input through reasoning system
        3. Provides response to user
        4. Continues interaction if needed
        
        Returns:
            Dict containing:
                - success: Whether the session completed successfully
                - results: Final results from reasoning system
                - context: Session context and interaction history
                
        Raises:
            ReasoningError: If reasoning system fails
            ConfigurationError: If agent is misconfigured
            DXAConnectionError: If I/O operations fail
        """
        context = {}
        try:
            # Get initial input
            response = await self.io.get_input("How can I help you today?")
            context['initial_input'] = response

            # Run reasoning cycle
            result = await self.reasoning.reason(context)
            
            # Check if we need user input
            if result.get("needs_user_input"):
                response = await self.io.get_input(result["user_prompt"])
                context['user_input'] = response
            
            return {
                "success": True,
                "results": result,
                "context": context
            }
            
        except (ReasoningError, ConfigurationError, DXAConnectionError) as e:
            self.logger.error("Interactive agent error: %s", str(e))
            return {
                "success": False,
                "error": str(e)
            }
