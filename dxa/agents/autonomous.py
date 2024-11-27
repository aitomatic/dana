"""Autonomous agent implementation."""

from typing import Dict, Any, Optional
from dxa.agents.base_agent import BaseAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.common.errors import DXAError

class AutonomousAgent(BaseAgent):
    """Base class for agents that operate independently."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: BaseReasoning,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None
    ):
        """Initialize autonomous agent."""
        config = {
            "llm": llm_config,
            "description": description,
            "mode": "autonomous"
        }
        
        super().__init__(name=name, config=config)
        
        self.reasoning = reasoning
        self.max_iterations = max_iterations
        self.iteration_count = 0

    async def run(self, task: str) -> Dict[str, Any]:
        """Run the autonomous agent's main loop.
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing results of agent's operation
        """
        context = {"task": task}
        try:
            self.iteration_count = 0
            
            while self._is_running:
                # Check iteration limit
                # flake8: noqa: E712
                if (self.max_iterations is not None and self.iteration_count >= self.max_iterations):
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
                    task
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
            
        except DXAError as e:  # More specific exceptions
            await self.handle_error(e)
            return {
                "success": False,
                "iterations": self.iteration_count,
                "error": str(e)
            } 