"""Autonomous agent implementation.

This module provides an agent implementation that operates independently without
requiring user interaction. It supports configurable iteration limits and maintains
its own execution state.

Example:
    ```python
    from dxa.agents.autonomous import AutonomousAgent
    from dxa.core.reasoning import ChainOfThoughtReasoning
    
    agent = AutonomousAgent(
        name="data_processor",
        llm_config={
            "model": "gpt-4",
            "api_key": "your-key"
        },
        reasoning=ChainOfThoughtReasoning(),
        max_iterations=10
    )
    
    result = await agent.run({
        "task": "analyze_data",
        "dataset": "sales_2023.csv",
        "objective": "find_trends"
    })
    ```
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.common.errors import DXAError

class AutonomousAgent(BaseAgent):
    """Base class for agents that operate independently.
    
    This agent type runs without user interaction, using its reasoning system
    to make decisions and process tasks autonomously. It supports iteration
    limits and progress tracking.
    
    Attributes:
        reasoning: Reasoning system instance
        max_iterations: Maximum number of reasoning cycles (None for unlimited)
        iteration_count: Current iteration count
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        reasoning: Reasoning system instance
        description: Optional agent description
        max_iterations: Optional maximum iterations (None for unlimited)
        
    Example:
        ```python
        agent = AutonomousAgent(
            name="data_analyzer",
            llm_config={"model": "gpt-4"},
            reasoning=ChainOfThoughtReasoning(),
            max_iterations=5
        )
        ```
    """
    
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
        
        This method executes the agent's reasoning cycle repeatedly until the task
        is complete, the iteration limit is reached, or the agent gets stuck.
        
        Args:
            task: The task/query to process
            
        Returns:
            Dict containing:
                - success: Whether the task completed successfully
                - iterations: Number of iterations performed
                - results: Results from final reasoning cycle
                
        Raises:
            DXAError: If agent encounters an error during execution
            
        Example:
            ```python
            result = await agent.run({
                "task": "analyze_text",
                "text": "Sample text to analyze",
                "objective": "sentiment"
            })
            ```
        """
        context = {"task": task}
        try:
            self.iteration_count = 0
            
            while self._is_running:
                # Check iteration limit
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
            
        except DXAError as e:
            await self.handle_error(e)
            return {
                "success": False,
                "iterations": self.iteration_count,
                "error": str(e)
            } 