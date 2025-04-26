"""Agent runtime for execution orchestration."""

from typing import Any, TYPE_CHECKING, Optional

from opendxa.execution.planning import Planner, Plan
from opendxa.execution.reasoning import Reasoner
from opendxa.base.execution.execution_context import ExecutionContext
if TYPE_CHECKING:
    from opendxa.agent.agent import Agent

class AgentRuntime:
    """Manages agent execution, coordinating between layers."""

    def __init__(self, agent: 'Agent',
                 planning_executor: Optional[Planner] = None,
                 reasoner: Optional[Reasoner] = None):
        self.agent = agent

        # Initialize executors with strategies
        self.reasoner = reasoner or \
            Reasoner(strategy=agent.reasoning_strategy)
        self.planning_executor = planning_executor or \
            Planner(strategy=agent.planning_strategy, lower_executor=self.reasoner)

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
        return signals[-1] if len(signals) > 0 else None

    async def cleanup(self) -> None:
        """Cleanup runtime resources."""
        # For now, nothing to clean up
        pass 