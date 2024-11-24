"""Console-based agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.base import BaseAgent
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base import BaseReasoning
from dxa.core.state import StateManager

class ConsoleAgent(BaseAgent):
    """Agent that interacts through console I/O."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize console agent."""
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            system_prompt=system_prompt,
            description=description
        )
        self.io = ConsoleIO()
        self.state_manager = StateManager()

    async def initialize(self) -> None:
        """Initialize agent resources."""
        await super().initialize()
        await self.io.initialize()
        self.state_manager.add_observation(
            content="Console agent initialized",
            source="console_agent"
        )
        self.logger.info("Console agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self.io.cleanup()
        await super().cleanup()
        self.state_manager.add_observation(
            content="Console agent cleaned up",
            source="console_agent"
        )
        self.logger.info("Console agent cleaned up")

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
            
        except Exception as e:
            self.state_manager.add_observation(
                content=f"Error in console agent: {str(e)}",
                source="console_agent",
                metadata={"error": str(e)}
            )
            return {
                "success": False,
                "error": str(e),
                "state_history": self.state_manager.get_state_history()
            } 