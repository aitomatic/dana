"""Agent runtime for execution orchestration."""

from typing import Any, TYPE_CHECKING, Optional

from opendxa.execution.planning import PlanExecutor, Plan
from opendxa.execution.reasoning import ReasoningExecutor
from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.base.execution.execution_types import ExecutionSignalType
if TYPE_CHECKING:
    from opendxa.agent.agent import Agent

class AgentRuntime:
    """Manages agent execution, coordinating between layers."""

    def __init__(self, agent: 'Agent',
                 planning_executor: Optional[PlanExecutor] = None,
                 reasoning_executor: Optional[ReasoningExecutor] = None):
        self.agent = agent

        # Initialize executors with strategies
        self.reasoning_executor = reasoning_executor or \
            ReasoningExecutor(strategy=agent.reasoning_strategy)
        self.planning_executor = planning_executor or \
            PlanExecutor(strategy=agent.planning_strategy, lower_executor=self.reasoning_executor)

    async def execute(self, plan: Plan, context: ExecutionContext) -> Any:
        """Execute plan and return result."""
        # Set current plan in context
        context.current_plan = plan

        # Make sure there are LLMs for each layer in the context
        assert context.workflow_llm is not None
        assert context.planning_llm is not None
        assert context.reasoning_llm is not None    

        # Execute plan with context
        signals = await self.planning_executor.execute(plan, context)

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