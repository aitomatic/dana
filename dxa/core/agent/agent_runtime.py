"""Agent runtime for execution orchestration."""

from typing import Any, Optional, TYPE_CHECKING
from ..workflow import WorkflowExecutor, WorkflowStrategy, Workflow
from ..planning import PlanExecutor, PlanningStrategy
from ..reasoning import ReasoningExecutor, ReasoningStrategy
from ..execution import ExecutionContext, ExecutionSignalType
if TYPE_CHECKING:
    from ..agent import Agent

class AgentRuntime:
    """Manages agent execution, coordinating between layers."""
    
    def __init__(self, agent: 'Agent',
                 workflow_strategy: Optional[WorkflowStrategy] = None,
                 planning_strategy: Optional[PlanningStrategy] = None,
                 reasoning_strategy: Optional[ReasoningStrategy] = None):
        self.agent = agent
        
        # Initialize executors with strategies
        self.reasoning_executor = ReasoningExecutor(
            strategy=reasoning_strategy or ReasoningStrategy.DEFAULT
        )
        self.plan_executor = PlanExecutor(
            reasoning_executor=self.reasoning_executor,
            strategy=planning_strategy or PlanningStrategy.DEFAULT
        )
        self.workflow_executor = WorkflowExecutor(
            plan_executor=self.plan_executor,
            strategy=workflow_strategy or WorkflowStrategy.DEFAULT
        )

    async def execute(self, workflow: Workflow, context: ExecutionContext) -> Any:
        """Execute workflow and return result."""
        # Set current workflow in context
        context.current_workflow = workflow
        
        # Execute workflow with context
        signals = await self.workflow_executor.execute_workflow(workflow, context)
        
        # Get final result from signals
        for signal in reversed(signals):
            if signal.type == ExecutionSignalType.RESULT:
                return signal.content
                
        return None

    async def cleanup(self) -> None:
        """Cleanup runtime resources."""
        # For now, nothing to clean up
        pass
