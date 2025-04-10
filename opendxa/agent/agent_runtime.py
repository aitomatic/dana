"""Agent runtime for execution orchestration."""

from typing import Any, TYPE_CHECKING, Optional

from ..execution.workflow import WorkflowExecutor, Workflow
from ..execution.planning import PlanExecutor
from ..execution.reasoning import ReasoningExecutor
from ..execution.execution_context import ExecutionContext
from ..execution.execution_types import ExecutionSignalType
if TYPE_CHECKING:
    from ..agent import Agent

class AgentRuntime:
    """Manages agent execution, coordinating between layers."""

    def __init__(self, agent: 'Agent',
                 workflow_executor: Optional[WorkflowExecutor] = None,
                 planning_executor: Optional[PlanExecutor] = None,
                 reasoning_executor: Optional[ReasoningExecutor] = None):
        self.agent = agent

        # Initialize executors with strategies
        self.reasoning_executor = reasoning_executor or \
            ReasoningExecutor(strategy=agent.reasoning_strategy)
        self.planning_executor = planning_executor or \
            PlanExecutor(strategy=agent.planning_strategy, lower_executor=self.reasoning_executor)
        self.workflow_executor = workflow_executor or \
            WorkflowExecutor(strategy=agent.workflow_strategy, lower_executor=self.planning_executor)

    async def execute(self, workflow: Workflow, context: ExecutionContext) -> Any:
        """Execute workflow and return result."""
        # Set current workflow in context
        context.current_workflow = workflow

        # Make sure there are LLMs for each layer in the context
        assert context.workflow_llm is not None
        assert context.planning_llm is not None
        assert context.reasoning_llm is not None    

        # Execute workflow with context
        signals = await self.workflow_executor.execute(workflow, context)

        # Get final result from signals
        # TODO: Handle multiple signals
        for signal in reversed(signals):
            if signal.type == ExecutionSignalType.DATA_RESULT:
                return signal.content

        return None

    async def cleanup(self) -> None:
        """Cleanup runtime resources."""
        # For now, nothing to clean up
        pass
