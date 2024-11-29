"""WebSocket-based agent implementation.

This module provides an agent implementation that communicates through WebSocket
connections. It enables real-time bidirectional communication and maintains
connection state.

Example:
    ```python
    from dxa.agents.websocket import WebSocketAgent
    from dxa.core.reasoning import ChainOfThoughtReasoning
    
    agent = WebSocketAgent(
        name="remote_solver",
        config={
            "model": "gpt-4",
            "api_key": "your-key"
        },
        reasoning=ChainOfThoughtReasoning(),
        websocket_url="wss://your-server.com/agent"
    )
    
    result = await agent.run({
        "task": "solve_problem",
        "data": {"problem": "..."}
    })
    ```
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.io.websocket import WebSocketIO
from dxa.common.errors import WebSocketError, DXAConnectionError
from dxa.core.reasoning import BaseReasoning, ChainOfThoughtReasoning
from dxa.agent.state import StateManager

class WebSocketAgent(BaseAgent):
    """Agent that interacts through WebSocket I/O."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        websocket_url: str,
        reasoning: Optional[BaseReasoning] = None,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0,
        max_iterations: Optional[int] = None
    ):
        """Initialize WebSocket agent."""
        super().__init__(
            name=name,
            config=config,
            max_iterations=max_iterations
        )
        
        self.reasoning = reasoning or ChainOfThoughtReasoning()
        self.io = WebSocketIO(
            url=websocket_url,
            max_retries=reconnect_attempts,
            retry_delay=reconnect_delay
        )
        self.state_manager = StateManager(name)

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's main loop.
        
        Args:
            task: Dictionary containing task configuration and parameters
            
        Returns:
            Dict containing:
                - success: Whether the task completed successfully
                - results: Results from reasoning system
                - state_history: History of observations and messages
        """
        try:
            context = task.copy()
            
            # Get initial input if needed
            if 'initial_input' not in context:
                response = await self.io.get_input(
                    "How can I help you today?"
                )
                context['initial_input'] = response
                self.state_manager.add_observation(
                    content=response,
                    source="user_input",
                    metadata={"type": "initial_input"}
                )

            # Main interaction loop
            while True:
                # Run reasoning cycle
                result = await self.reasoning.reason(context, task)
                
                # Record reasoning result
                self.state_manager.add_observation(
                    content=result,
                    source="reasoning",
                    metadata={"type": "reasoning_result"}
                )
                
                # Check if we need user input
                if result.get("needs_user_input"):
                    response = await self.io.get_input(result["user_prompt"])
                    context['user_input'] = response
                    self.state_manager.add_observation(
                        content=response,
                        source="user_input",
                        metadata={"type": "follow_up_input"}
                    )
                
                # Check if we're done
                if result.get("interaction_complete"):
                    await self.io.send_message("Interaction complete. Goodbye!")
                    break
            
            return {
                "success": True,
                "results": result,
                "state_history": {
                    "observations": self.state_manager.observations,
                    "messages": self.state_manager.messages
                }
            }
            
        except (WebSocketError, DXAConnectionError) as e:
            self.logger.error("WebSocket error during run: %s", str(e))
            self.state_manager.add_observation(
                content=f"WebSocket error: {str(e)}",
                source="websocket_agent",
                metadata={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e),
                "state_history": {
                    "observations": self.state_manager.observations,
                    "messages": self.state_manager.messages
                }
            } 