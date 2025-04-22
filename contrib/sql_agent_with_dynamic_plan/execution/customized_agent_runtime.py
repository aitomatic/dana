from opendxa.execution.agent_runtime import AgentRuntime
from opendxa.execution.planning import Plan
from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.execution.reasoning import ReasoningExecutor
from contrib.sql_agent_with_dynamic_plan.execution.planning.dynamic_plan_executor import DynamicPlanExecutor
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from opendxa.agent import Agent

class CustomizedAgentRuntime(AgentRuntime):
    def __init__(self, agent: 'Agent',
                 planning_executor: Optional[DynamicPlanExecutor] = None,
                 reasoning_executor: Optional[ReasoningExecutor] = None):
        self.agent = agent

        # Initialize executors with strategies
        self.reasoning_executor = reasoning_executor or \
            ReasoningExecutor(strategy=agent.reasoning_strategy)
        self.planning_executor = planning_executor or \
            DynamicPlanExecutor(strategy=agent.planning_strategy, lower_executor=self.reasoning_executor)
