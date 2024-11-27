"""WebSocket-based agent implementation."""

from typing import Dict, Any
from dxa.agents.base_agent import BaseAgent
from dxa.core.io.websocket import WebSocketIO
from dxa.common.errors import WebSocketError, DXAConnectionError
from dxa.core.reasoning import BaseReasoning
from dxa.agents.state import StateManager

class WebSocketAgent(BaseAgent):
    """Agent that interacts through WebSocket I/O."""
    
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
        """Initialize agent resources."""
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
        """Clean up agent resources."""
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
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing results of agent's operation
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