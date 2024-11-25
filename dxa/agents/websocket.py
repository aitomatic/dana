"""WebSocket-based agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.base import BaseAgent
from dxa.core.io.websocket import WebSocketIO, WebSocketError
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.core.state import StateManager

class WebSocketAgent(BaseAgent):
    """Agent that interacts through WebSocket I/O."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        websocket_url: str,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0
    ):
        """Initialize WebSocket agent."""
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            system_prompt=system_prompt,
            description=description
        )
        self.io = WebSocketIO(
            websocket_url=websocket_url,
            reconnect_attempts=reconnect_attempts,
            reconnect_delay=reconnect_delay
        )
        self.state_manager = StateManager()

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
        except WebSocketError as e:
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
        except Exception as e:
            self.state_manager.add_observation(
                content=f"Cleanup error: {str(e)}",
                source="websocket_agent",
                metadata={"error": str(e)}
            )
            raise

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's main loop."""
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
                result = await self.reasoning.reason(context, "Process user interaction")
                
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
                "state_history": self.state_manager.get_state_history()
            }
            
        except WebSocketError as e:
            self.state_manager.add_observation(
                content=f"WebSocket error: {str(e)}",
                source="websocket_agent",
                metadata={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e),
                "state_history": self.state_manager.get_state_history()
            }
        except Exception as e:
            self.state_manager.add_observation(
                content=f"Runtime error: {str(e)}",
                source="websocket_agent",
                metadata={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e),
                "state_history": self.state_manager.get_state_history()
            } 