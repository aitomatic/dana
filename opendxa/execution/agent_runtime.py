"""Agent runtime for execution orchestration."""

from typing import Any, TYPE_CHECKING, Optional, NamedTuple
import logging

from opendxa.execution.planning import Planner, Plan
from opendxa.execution.reasoning import Reasoner
from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.base.state.execution_state import ExecutionStatus
from opendxa.base.resource.llm_resource import LLMResource
from opendxa.base.execution.execution_types import ExecutionNode
if TYPE_CHECKING:
    from opendxa.agent.agent import Agent

log = logging.getLogger(__name__)

# Define ExecutionResult here
class ExecutionResult(NamedTuple):
    """Holds the result of executing a single node."""
    node_id: str
    result: Any

class AgentRuntime:
    """Manages agent execution, coordinating between layers."""

    def __init__(self, agent: 'Agent',
                 planning_llm: LLMResource,
                 reasoning_llm: LLMResource,
                 planning_executor: Optional[Planner] = None,
                 reasoner: Optional[Reasoner] = None):
        self.agent = agent
        self._planning_llm = planning_llm
        self._reasoning_llm = reasoning_llm

        # Initialize executors with strategies and pass the appropriate LLM
        self.reasoner = reasoner or \
            Reasoner(
                strategy=agent.reasoning_strategy,
                reasoning_llm=self._reasoning_llm  # Pass reasoning LLM
            )
        self.planning_executor = planning_executor or \
            Planner(
                strategy=agent.planning_strategy, 
                lower_executor=self.reasoner,
                planning_llm=self._planning_llm  # Pass planning LLM
            )

    async def execute(self, plan: Plan, context: ExecutionContext) -> Any:
        """Execute plan and return result."""
        # Set current plan in context
        context.current_plan = plan

        # LLMs are now instance variables, no need to check context
        # assert context.planning_llm is not None
        # assert context.reasoning_llm is not None

        log.info(f"Starting execution for plan: {plan.id}")
        context.reset_execution_state()
        context.set('execution.status', ExecutionStatus.RUNNING)

        # Execute plan with context
        signals = await self.planning_executor.execute(plan, context)

        # Get final result from signals
        # TODO: Handle multiple signals
        return signals[-1] if len(signals) > 0 else None

    async def cleanup(self) -> None:
        """Cleanup runtime resources."""
        # For now, nothing to clean up
        pass

    async def _execute_planning_node(self, node: ExecutionNode, context: ExecutionContext) -> ExecutionResult:
        """Execute a planning node."""
        log.info(f"Executing planning node: {node.node_id}")
        prompt = self._build_planning_prompt(node, context)
        # Use the instance LLM
        result = await self._planning_llm.acall(prompt)
        log.info(f"Planning node {node.node_id} result: {result}")
        return ExecutionResult(node_id=node.node_id, result=result)

    async def _execute_reasoning_node(self, node: ExecutionNode, context: ExecutionContext) -> ExecutionResult:
        """Execute a reasoning node."""
        log.info(f"Executing reasoning node: {node.node_id}")
        prompt = self._build_reasoning_prompt(node, context)
        # Use the instance LLM
        result = await self._reasoning_llm.acall(prompt)
        log.info(f"Reasoning node {node.node_id} result: {result}")
        return ExecutionResult(node_id=node.node_id, result=result) 