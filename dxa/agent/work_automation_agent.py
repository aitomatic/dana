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
        self.reasoning = reasoning or OODAReasoning()
        self._is_running = True
        
        config = {
            "llm": llm_config,
            "description": description,
            "logging": llm_config.get("logging", {})
        }
        
        super().__init__(
            name=name,
            config=config,
            max_iterations=max_iterations
        )
        
        self.workflow = workflow
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run the automation workflow.
        
        Args:
            task: Dictionary containing task configuration and parameters
            
        Returns:
            Dict containing:
                - success: Whether workflow completed successfully
                - results: Results from workflow execution
                - workflow_state: Final state of workflow execution
        """
        context = task.copy()
        workflow_state = {}
        
        try:
            self.iteration_count = 0
            
            while self._is_running:
                # Check iteration limit
                if (self.max_iterations is not None and self.iteration_count >= self.max_iterations):
                    self.logger.log_completion(
                        prompt="Iteration check",
                        response="Reached maximum iterations",
                        tokens=0
                    )
                    break
                    
                # Run workflow step
                self.iteration_count += 1
                result = await self.reasoning.reason(context, task)
                
                # Update workflow state
                workflow_state[f"step_{self.iteration_count}"] = result
                context.update(result)
                
                if result.get("workflow_complete"):
                    self.logger.log_completion(
                        prompt="Workflow status",
                        response="Workflow completed successfully",
                        tokens=0
                    )
                    break
                    
                if result.get("is_stuck"):
                    self.logger.log_error(
                        error_type="workflow_stuck",
                        message=f"Workflow is stuck: {result.get('stuck_reason')}"
                    )
                    break
                    
            return {
                "success": True,
                "results": result,
                "workflow_state": workflow_state
            }
            
        except (ValueError, TypeError) as e:
            self.logger.log_error(
                error_type="automation_error",
                message=f"Automation workflow error: {str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "workflow_state": workflow_state
            }