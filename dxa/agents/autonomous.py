"""Autonomous agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.base import BaseAgent
from dxa.core.reasoning.base import BaseReasoning

class AutonomousAgent(BaseAgent):
    """Base class for agents that operate independently."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None
    ):
        """Initialize autonomous agent.
        
        Args:
            name: Name of this agent
            llm_config: Configuration for the agent's LLM
            reasoning: Reasoning pattern to use
            system_prompt: Optional system prompt for the LLM
            description: Optional description of this agent
            max_iterations: Optional maximum number of iterations
        """
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=reasoning,
            system_prompt=system_prompt,
            description=description
        )
        self.max_iterations = max_iterations
        self.iteration_count = 0

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the autonomous agent's main loop."""
        try:
            self.iteration_count = 0
            
            while self._is_running:
                # Check iteration limit
                if (
                    self.max_iterations is not None 
                    and self.iteration_count >= self.max_iterations
                ):
                    self.logger.info("Reached maximum iterations")
                    break
                
                # Run reasoning cycle
                self.iteration_count += 1
                self.logger.debug(
                    "Starting iteration %d/%s", 
                    self.iteration_count,
                    self.max_iterations or "∞"
                )
                
                result = await self.reasoning.reason(
                    context,
                    f"Autonomous iteration {self.iteration_count}"
                )
                
                # Update context with results
                context.update(result)
                
                # Check if task is complete
                if result.get("task_complete"):
                    self.logger.info("Task completed successfully")
                    break
                
                # Check if we're stuck
                if result.get("is_stuck"):
                    self.logger.warning("Agent is stuck: %s", result.get("stuck_reason"))
                    break
            
            return {
                "success": True,
                "iterations": self.iteration_count,
                "results": result
            }
            
        except Exception as e:
            await self.handle_error(e)
            return {
                "success": False,
                "iterations": self.iteration_count,
                "error": str(e)
            } 