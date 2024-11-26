"""Console-based agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.base_agent import BaseAgent
from dxa.core.io.base_io import BaseIO
from dxa.core.io.console import ConsoleIO
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningStatus
from dxa.core.resources.base_resource import BaseResource
from dxa.core.common.exceptions import (
    DXAError,
    ReasoningError,
    ResourceError,
    ConfigurationError
)

class InteractiveAgent(BaseAgent):
    """Agent that interacts through console I/O."""
    
    def __init__(
        self,
        name: str,
        reasoning: BaseReasoning,
        llm_config: Dict[str, Any],
        resources: Optional[Dict[str, BaseResource]] = None,
        agent_prompt: Optional[str] = None,
        description: Optional[str] = None,
        io: Optional[BaseIO] = ConsoleIO()
    ):
        """Initialize console agent."""
        super().__init__(
            name=name,
            reasoning=reasoning,
            llm_config=llm_config,
            resources=resources,
            agent_prompt=agent_prompt,
            description=description
        )
        self.io = io

    async def initialize(self) -> None:
        """Initialize agent resources."""
        await super().initialize()
        await self.io.initialize()
        self.logger.info("Console agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await super().cleanup()
        await self.io.cleanup()
        self.logger.info("Console agent cleaned up")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent's main loop.
        
        Args:
            context: Must contain either:
                - task_spec: The problem/task specification
                - or domain and parameters for the task
        """
        try:
            # Get task specification if not provided
            if 'task_spec' not in context:
                task_spec = await self.io.get_input(
                    "What would you like help with?"
                )
                context['task_spec'] = task_spec

            # Main interaction loop
            while True:
                # Run reasoning cycle
                result = await self.reasoning.reason(context, context['task_spec'])
                
                # Handle result based on status
                match result.status:
                    case ReasoningStatus.NEED_INFO:
                        if result.user_context:
                            await self.io.send_message(result.user_context)
                        response = await self.io.get_input(result.user_prompt)
                        context['user_input'] = response
                    
                    case ReasoningStatus.NEED_EXPERT:
                        expert_response = await self.use_expert(
                            result.expert_domain,
                            result.expert_request
                        )
                        context['expert_response'] = expert_response
                    
                    case ReasoningStatus.COMPLETE:
                        message = result.final_answer or "No explicit answer provided"
                        if result.explanation:
                            message = f"{message}\n\nExplanation: {result.explanation}"
                        
                        await self.io.send_message(message)
                        await self.io.send_message("Task completed. Goodbye!")
                        break
                    
                    case ReasoningStatus.ERROR:
                        error_msg = result.reason or "An unknown error occurred"
                        if result.suggestion:
                            error_msg = f"{error_msg}\n\nSuggestion: {result.suggestion}"
                        
                        await self.io.send_message(error_msg)
                        break
                    
                    case _:
                        await self.io.send_message(
                            "I encountered an unexpected situation and need to stop. "
                            "Please try again with a different request."
                        )
                        break
            
            return {
                "success": result.status == ReasoningStatus.COMPLETE,
                "status": result.status,
                "result": result
            }
            
        except (ConfigurationError, ReasoningError, ResourceError, DXAError) as e:
            error_msg = f"{type(e).__name__} error: {str(e)}"
            await self.io.send_message(error_msg)
            self.logger.error(error_msg)
            return {
                "success": False,
                "status": ReasoningStatus.ERROR,
                "error": str(e)
            }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 

class ConsoleAgent(InteractiveAgent):
    """Agent that interacts through console I/O."""
    def __init__(self, *args, **kwargs):
        """Initialize console agent."""
        super().__init__(*args, io=ConsoleIO(), **kwargs)
