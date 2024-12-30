"""Agent runtime for execution orchestration."""

from typing import Any, Optional, TYPE_CHECKING
from ..workflow import WorkflowExecutor, WorkflowStrategy, Workflow
from ..planning import PlanExecutor, PlanningStrategy
from ..reasoning import ReasoningExecutor, ReasoningStrategy
from ..state import WorldState, ExecutionState
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
            strategy=reasoning_strategy or ReasoningStrategy.DIRECT
        )
        self.plan_executor = PlanExecutor(
            reasoning_executor=self.reasoning_executor,
            strategy=planning_strategy or PlanningStrategy.DIRECT
        )
        self.workflow_executor = WorkflowExecutor(
            plan_executor=self.plan_executor,
            strategy=workflow_strategy or WorkflowStrategy.DEFAULT
        )

    async def execute(self, workflow: Workflow) -> Any:
        """Execute workflow and return result."""
        context = ExecutionContext(
            agent_state=self.agent.state,
            world_state=WorldState(),
            execution_state=ExecutionState(),
            current_workflow=workflow,
            workflow_llm=self.agent.workflow_llm,  # Could be specialized
            planning_llm=self.agent.planning_llm,  # Could be specialized
            reasoning_llm=self.agent.agent_llm     # Default LLM for now
        )

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
