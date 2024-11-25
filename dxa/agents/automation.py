"""Automation agent implementation."""

from typing import Dict, Any, Optional
import asyncio
from dxa.agents.autonomous import AutonomousAgent
from dxa.core.reasoning.ooda import OODALoopReasoning

class AutomationAgent(AutonomousAgent):
    """Agent for automating tasks and workflows."""
    
    def __init__(
        self,
        name: str,
        llm_config: Dict[str, Any],
        workflow: Dict[str, Any],
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize automation agent.
        
        Args:
            name: Name of this agent
            llm_config: Configuration for the agent's LLM
            workflow: Workflow definition including steps and validation
            system_prompt: Optional system prompt for the LLM
            description: Optional description of this agent
            max_retries: Maximum number of retry attempts per step
            retry_delay: Delay between retries in seconds
        """
        super().__init__(
            name=name,
            llm_config=llm_config,
            reasoning=OODALoopReasoning(),  # Automation uses OODA loop
            system_prompt=system_prompt or self._get_default_system_prompt(),
            description=description
        )
        self.workflow = workflow
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.current_step = None
        self.step_results = []

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for automation."""
        return """You are an automation agent that executes workflows.
        For each step:
        1. Observe the current state and requirements
        2. Orient yourself in the workflow context
        3. Decide on the specific actions needed
        4. Act carefully and verify results
        
        Always validate results and handle errors gracefully.
        If stuck, provide clear error messages and state."""

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the automation workflow.
        
        Args:
            context: Initial context including workflow state
            
        Returns:
            Dict containing results of workflow execution
        """
        try:
            self.logger.info("Starting workflow execution")
            
            # Initialize workflow state
            workflow_state = {
                "workflow": self.workflow,
                "current_step": None,
                "step_results": [],
                "context": context
            }
            
            # Execute workflow steps
            for step in self.workflow["steps"]:
                self.current_step = step
                step_result = await self._execute_step(step, workflow_state)
                
                if not step_result["success"]:
                    self.logger.error(
                        "Workflow failed at step '%s': %s",
                        step["name"],
                        step_result["error"]
                    )
                    return {
                        "success": False,
                        "error": f"Step '{step['name']}' failed: {step_result['error']}",
                        "workflow_state": workflow_state
                    }
                
                # Update workflow state
                workflow_state["step_results"].append(step_result)
                workflow_state["context"].update(step_result.get("context", {}))
            
            self.logger.info("Workflow completed successfully")
            return {
                "success": True,
                "workflow_state": workflow_state
            }
            
        except (ValueError, RuntimeError, KeyError, AttributeError) as e:
            await self.handle_error(e)
            return {
                "success": False,
                "error": str(e),
                "workflow_state": workflow_state
            }

    async def _execute_step(
        self,
        step: Dict[str, Any],
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step.
        
        Args:
            step: Step definition
            workflow_state: Current workflow state
            
        Returns:
            Dict containing step execution results
        """
        self.logger.info("Executing step: %s", step["name"])
        
        for attempt in range(self.max_retries):
            try:
                # Update context with current step
                context = {
                    **workflow_state["context"],
                    "current_step": step,
                    "attempt": attempt + 1
                }
                
                # Run reasoning cycle for this step
                result = await self.reasoning.reason(
                    context,
                    f"Execute step: {step['name']}"
                )
                
                # Validate step results
                if step.get("validation"):
                    validation_result = await self._validate_step(
                        step,
                        result,
                        context
                    )
                    if not validation_result["success"]:
                        raise ValueError(validation_result["error"])
                
                return {
                    "success": True,
                    "step": step["name"],
                    "result": result,
                    "context": context
                }
                
            except Exception as e:
                self.logger.warning(
                    "Step '%s' attempt %d failed: %s",
                    step["name"],
                    attempt + 1,
                    str(e)
                )
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "step": step["name"],
                        "error": str(e),
                        "context": context
                    }
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def _validate_step(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate step execution results.
        
        Args:
            step: Step definition
            result: Step execution result
            context: Current context
            
        Returns:
            Dict containing validation results
        """
        validation = step["validation"]
        try:
            # Run validation function if provided
            if callable(validation):
                is_valid = validation(result, context)
            # Check required fields
            elif isinstance(validation, dict):
                is_valid = all(
                    result.get(field) == validation[field]
                    for field in validation
                )
            else:
                raise ValueError(f"Invalid validation type: {type(validation)}")
            
            return {
                "success": is_valid,
                "error": None if is_valid else "Validation failed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Validation error: {str(e)}"
            } 

    async def handle_error(self, error: Exception) -> None:
        """Handle workflow execution errors.
        
        Args:
            error: The exception that was raised
        """
        self.logger.error("Workflow error: %s", str(error)) 