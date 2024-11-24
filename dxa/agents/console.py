"""Console-based agent implementation."""

from typing import Dict, Any, Optional, List
from dxa.agents.base import BaseAgent
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base import BaseReasoning
from dxa.core.expertise import ExpertResource

class ConsoleAgent(BaseAgent):
    """Agent that interacts through console I/O."""
    
    def __init__(
        self,
        name: str,
        reasoning: BaseReasoning,
        internal_llm_config: Dict[str, Any],
        expert_resources: Optional[List[ExpertResource]] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize console agent."""
        super().__init__(
            name=name,
            reasoning=reasoning,
            internal_llm_config=internal_llm_config,
            expert_resources=expert_resources,
            system_prompt=system_prompt,
            description=description
        )
        self.io = ConsoleIO()

    async def initialize(self) -> None:
        """Initialize agent resources."""
        await super().initialize()
        await self.io.initialize()
        self.logger.info("Console agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self.io.cleanup()
        await super().cleanup()
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

            # Main interaction loop
            while True:
                # Run reasoning cycle
                result = await self.reasoning.reason(context, context['initial_input'])
                
                # Check if we need user input
                if result.get("needs_user_input"):
                    response = await self.io.get_input(result["user_prompt"])
                    context['user_input'] = response
                
                # Check if we need to use any experts
                if result.get("needs_expert"):
                    expert_request = result["expert_request"]
                    expert_response = await self.use_expert(
                        expert_request["domain"],
                        expert_request["request"]
                    )
                    context['expert_response'] = expert_response
                
                # Check if we're done
                if result.get("interaction_complete"):
                    await self.io.send_message("Interaction complete. Goodbye!")
                    break
            
            return {
                "success": True,
                "results": result
            }
            
        except Exception as e:
            self.logger.error("Error in console agent: %s", str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 