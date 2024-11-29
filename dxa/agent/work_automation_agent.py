"""Work automation agent implementation.

This module provides an agent implementation specialized for workflow automation.
It extends the base agent with workflow tracking, validation capabilities, and 
structured work processes.

Example:
    ```python
    from dxa.agents.automation import WorkAutomationAgent
    
    # Define workflow steps
    workflow = {
        "name": "data_processing",
        "steps": [
            {
                "name": "collect",
                "validation": lambda r: len(r.get("data", [])) > 0
            },
            {
                "name": "process",
                "validation": lambda r: "processed_data" in r
            }
        ]
    }
    
    agent = WorkAutomationAgent(
        name="data_processor",
        llm_config={"model": "gpt-4"},
        workflow=workflow,
        max_retries=3
    )
    
    result = await agent.run({
        "input_source": "data.csv",
        "output_format": "json"
    })
    ```
"""

from typing import Dict, Any, Optional
from dxa.agent.base_agent import BaseAgent
from dxa.core.reasoning.ooda import OODAReasoning
from dxa.core.reasoning import BaseReasoning

class WorkAutomationAgent(BaseAgent):
    """Agent for automating structured work processes and workflows.
    
    This agent type specializes in executing predefined workflows with:
    - Step-by-step workflow execution
    - Validation at each step
    - Retry mechanisms for failed steps
    - State tracking throughout workflow
    - OODA-loop based reasoning for structured processes
    
    Attributes:
        All attributes inherited from BaseAgent
        workflow: Workflow definition dictionary
        max_retries: Maximum retry attempts per step
        retry_delay: Delay between retries in seconds
        current_step: Index of current workflow step
        
    Args:
        name: Agent identifier
        llm_config: LLM configuration dictionary
        workflow: Workflow definition dictionary
        reasoning: Optional reasoning system (defaults to OODAReasoning)
        description: Optional agent description
        max_retries: Maximum retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)
        max_iterations: Optional maximum iterations
    """
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        workflow: Dict[str, Any],
        reasoning: Optional[BaseReasoning] = None,
        description: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_iterations: Optional[int] = None
    ):
        """Initialize work automation agent."""
        config = {
            "llm": llm_config,
            "description": description
        }
        
        super().__init__(
            name=name,
            config=config,
            reasoning=reasoning or OODAReasoning(),
            mode="automation",
            max_iterations=max_iterations
        )
        
        self.workflow = workflow
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.current_step = 0

    async def _pre_execute(self, context: Dict[str, Any]) -> None:
        """Validate workflow and prepare for execution.
        
        Args:
            context: Initial execution context
            
        Raises:
            ValueError: If workflow definition is invalid
        """
        if not self.workflow.get("steps"):
            raise ValueError("Workflow must contain steps")
            
        # Add workflow info to context
        context.update({
            "workflow_name": self.workflow["name"],
            "total_steps": len(self.workflow["steps"]),
            "current_step": 0
        })

    async def _post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process workflow results.
        
        Args:
            result: Results from final reasoning iteration
            
        Returns:
            Processed results with workflow metadata
        """
        result.update({
            "agent_type": "work_automation",
            "execution_mode": self.mode,
            "workflow_name": self.workflow["name"],
            "completed_steps": self.current_step
        })
        return result

    async def _should_continue(self, result: Dict[str, Any]) -> bool:
        """Check if workflow should continue.
        
        Args:
            result: Results from last reasoning iteration
            
        Returns:
            True if there are more steps to process, False otherwise
        """
        # Check completion
        if result.get("task_complete") or result.get("is_stuck"):
            return False
            
        # Check if current step passed validation
        current_step = self.workflow["steps"][self.current_step]
        if current_step.get("validation"):
            if not current_step["validation"](result):
                # Retry logic could be implemented here
                return False
                
        # Move to next step
        self.current_step += 1
        return self.current_step < len(self.workflow["steps"])

    async def _reasoning_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one workflow step.
        
        Args:
            context: Current execution context
            
        Returns:
            Dict containing step results and validation status
        """
        # Get current step definition
        step = self.workflow["steps"][self.current_step]
        
        # Add step info to context
        context.update({
            "current_step": self.current_step,
            "step_name": step["name"]
        })
        
        # Run reasoning for this step
        result = await self.reasoning.reason(context)
        
        # Add step completion info
        result["step_complete"] = True
        result["step_name"] = step["name"]
        
        return result