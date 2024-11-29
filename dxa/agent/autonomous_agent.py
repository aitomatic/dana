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

class AutonomousAgent(BaseAgent):
    """Base class for agents that operate independently.
    
    This agent type runs without user interaction, using its reasoning system
    to make decisions and process tasks autonomously. It supports iteration
    limits and progress tracking.
    
    The key differences from BaseAgent are:
    1. Stricter validation of task parameters
    2. More detailed progress reporting
    3. Automatic handling of stuck states
    
    Attributes:
        All attributes inherited from BaseAgent
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        reasoning: Optional reasoning system instance
        description: Optional agent description
        max_iterations: Optional maximum iterations (None for unlimited)
    """
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        description: Optional[str] = None,
        max_iterations: Optional[int] = None
    ):
        """Initialize autonomous agent."""
        config = {
            "llm": llm_config,
            "description": description
        }
        
        super().__init__(
            name=name,
            config=config,
            reasoning=reasoning,
            mode="autonomous",
            max_iterations=max_iterations
        )

    async def _pre_execute(self, context: Dict[str, Any]) -> None:
        """Validate task parameters before execution.
        
        Args:
            context: Initial execution context to validate
            
        Raises:
            ValueError: If required task parameters are missing
        """
        required_params = ["objective"]
        missing = [p for p in required_params if p not in context]
        if missing:
            raise ValueError(f"Missing required task parameters: {missing}")

    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process results after execution.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results with additional metadata
        """
        # Add execution metadata
        result["agent_type"] = "autonomous"
        result["execution_mode"] = self.mode
        return result

    async def _should_continue(self, result: Dict[str, Any]) -> bool:
        """Check if execution should continue.
        
        Args:
            result: Results from last reasoning iteration
            
        Returns:
            False if task is complete or agent is stuck, True otherwise
        """
        # Stop if task is complete or we're stuck
        if result.get("task_complete") or result.get("is_stuck"):
            return False
            
        # Continue otherwise
        return True 