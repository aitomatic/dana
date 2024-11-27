"""Console-based agent implementation."""

from typing import Optional, Dict, Any
from dxa.agents.base_agent import BaseAgent
from dxa.core.io.base_io import BaseIO
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.agents.config import AgentConfig
from dxa.common.errors import ReasoningError, ConfigurationError, DXAConnectionError

class InteractiveAgent(BaseAgent):
    """Agent that interacts through console I/O."""
    
    def __init__(
        self,
        config: AgentConfig,
        reasoning: BaseReasoning,
        io: Optional[BaseIO] = None
    ):
        """Initialize interactive agent."""
        super().__init__(
            name=config.name,
            config=config.llm_config.__dict__,
            mode="interactive"
        )
        self.reasoning = reasoning
        self.io = io or ConsoleIO()

    async def run(self, task: str) -> Dict[str, Any]:
        """Run the interactive agent's main loop.
        
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

            # Run reasoning cycle
            result = await self.reasoning.reason(context, task)
            
            # Check if we need user input
            if result.get("needs_user_input"):
                response = await self.io.get_input(result["user_prompt"])
                context['user_input'] = response
            
            return {
                "success": True,
                "results": result,
                "context": context
            }
            
        except (ReasoningError, ConfigurationError, ValueError, DXAConnectionError) as e:  # More specific exceptions
            self.logger.error("Interactive agent error: %s", str(e))
            return {
                "success": False,
                "error": str(e)
            }
