"""Interactive agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.base import BaseAgent
from dxa.core.io.base import BaseIO
from dxa.core.io.console import ConsoleIO
from dxa.core.resources.human import HumanUserResource
from dxa.core.reasoning.base import BaseReasoning

class InteractiveAgent(BaseAgent):
    """Base class for agents that interact with users."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        io: Optional[BaseIO] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize interactive agent.
        
        Args:
            name: Name of this agent
            llm_config: Configuration for the agent's LLM
            reasoning: Reasoning pattern to use
            io: Optional I/O handler (defaults to ConsoleIO)
            system_prompt: Optional system prompt for the LLM
            description: Optional description of this agent
        """
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            system_prompt=system_prompt,
            description=description
        )
        
        # Set up I/O
        self.io = io or ConsoleIO()
        
        # Create user resource
        self.user = HumanUserResource(
            name=f"{name}_user",
            role="user",
            permissions={
                "interact": True,
                "provide_input": True,
                "receive_output": True
            },
            io=self.io
        )

    async def initialize(self) -> None:
        """Initialize agent resources."""
        await super().initialize()
        await self.io.initialize()
        self.logger.info("Interactive agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self.io.cleanup()
        await super().cleanup()
        self.logger.info("Interactive agent cleaned up")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the interactive agent's main loop.
        
        Args:
            context: Initial context for the agent
            
        Returns:
            Dict containing results of agent's operation
        """
        try:
            # Get initial input if needed
            if 'initial_input' not in context:
                response = await self.user.query({
                    "message": "How can I help you today?",
                    "require_response": True
                })
                if response["success"]:
                    context['initial_input'] = response["response"]
                else:
                    raise RuntimeError("Failed to get initial input")

            # Main interaction loop
            while self._is_running:
                # Run reasoning cycle
                result = await self.reasoning.reason(context, "Process user interaction")
                
                # Check if we need user input
                if result.get("needs_user_input"):
                    response = await self.user.query({
                        "message": result["user_prompt"],
                        "require_response": True
                    })
                    if response["success"]:
                        context['user_input'] = response["response"]
                    else:
                        self.logger.warning("Failed to get user input")
                
                # Check if we're done
                if result.get("interaction_complete"):
                    await self.user.query({
                        "message": "Interaction complete. Goodbye!",
                        "require_response": False
                    })
                    break
            
            return {
                "success": True,
                "results": result
            }
            
        except KeyboardInterrupt:
            self.logger.info("Interaction interrupted by user")
            return {
                "success": False,
                "error": "Interrupted by user"
            }
        except Exception as e:
            await self.handle_error(e)
            return {
                "success": False,
                "error": str(e)
            } 