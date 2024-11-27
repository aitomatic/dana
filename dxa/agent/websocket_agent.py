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

from typing import Dict, Any
from dxa.agent.base_agent import BaseAgent
from dxa.core.io.websocket import WebSocketIO
from dxa.common.errors import WebSocketError, DXAConnectionError
from dxa.core.reasoning import BaseReasoning
from dxa.agent.state import StateManager

class WebSocketAgent(BaseAgent):
    """Agent that interacts through WebSocket I/O.
    
    This agent type provides real-time communication capabilities through WebSocket
    connections. It handles connection management, reconnection attempts, and
    maintains state across interactions.
    
    Attributes:
        reasoning: Reasoning system instance
        io: WebSocket I/O interface
        state_manager: State tracking manager
        
    Args:
        name: Agent identifier
        config: Configuration dictionary
        reasoning: Reasoning system instance
        websocket_url: WebSocket server URL
        reconnect_attempts: Max reconnection attempts (default: 3)
        reconnect_delay: Seconds between attempts (default: 1.0)
        
    Example:
        ```python
        agent = WebSocketAgent(
            name="remote_agent",
            config={"model": "gpt-4"},
            reasoning=ChainOfThoughtReasoning(),
            websocket_url="wss://server.com/agent"
        )
        ```
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        reasoning: BaseReasoning,
        websocket_url: str,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0
    ):
        """Initialize WebSocket agent."""
        super().__init__(
            name=name,
            config=config,
            mode="websocket"
        )
        
        self.reasoning = reasoning
        self.io = WebSocketIO(
            url=websocket_url,
            max_retries=reconnect_attempts,
            retry_delay=reconnect_delay
        )
        self.state_manager = StateManager(name)

    async def initialize(self) -> None:
        """Initialize agent resources.
        
        Sets up WebSocket connection and initializes resources.
        
        Raises:
            WebSocketError: If WebSocket connection fails
            DXAConnectionError: If connection setup fails
        """
        try:
            await super().initialize()
            await self.io.initialize()
            self.state_manager.add_observation(
                content="WebSocket agent initialized",
                source="websocket_agent"
            )
            self.logger.info("WebSocket agent initialized")
        except (WebSocketError, DXAConnectionError) as e:
            self.logger.error("WebSocket initialization failed: %s", str(e))
            self.state_manager.add_observation(
                content=f"Initialization failed: {str(e)}",
                source="websocket_agent",
                metadata={"error": str(e)}
            )
            raise

    async def cleanup(self) -> None:
        """Clean up agent resources.
        
        Closes WebSocket connection and cleans up resources.
        
        Raises:
            WebSocketError: If WebSocket cleanup fails
            DXAConnectionError: If connection cleanup fails
        """
        try:
            await self.io.cleanup()
            await super().cleanup()
            self.state_manager.add_observation(
                content="WebSocket agent cleaned up",
                source="websocket_agent"
            )
            self.logger.info("WebSocket agent cleaned up")
        except (WebSocketError, DXAConnectionError, ValueError) as e:
            self.logger.error("WebSocket cleanup failed: %s", str(e))
            self.state_manager.add_observation(
                content=f"Cleanup error: {str(e)}",
                source="websocket_agent",
                metadata={"error": str(e)}
            )
            raise

    async def run(self, task: str) -> Dict[str, Any]:
        """Run the agent's main loop.
        
        Manages WebSocket communication and task execution.
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing:
                - success: Whether the task completed successfully
                - results: Results from reasoning system
                - state_history: History of observations and messages
                
        Raises:
            WebSocketError: If WebSocket communication fails
            DXAConnectionError: If connection is lost
            
        Example:
            ```python
            result = await agent.run({
                "task": "process_data",
                "data": {"values": [1, 2, 3]}
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