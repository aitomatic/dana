"""Plan executor implementation."""

from typing import Optional
from opendxa.base.execution.base_executor import BaseExecutor
from opendxa.execution.planning.plan import Plan
from opendxa.execution.planning.plan_strategy import PlanStrategy
from opendxa.execution.reasoning import Reasoner, ReasoningStrategy
from opendxa.execution.planning.plan_factory import PlanFactory

class Planner(BaseExecutor[PlanStrategy, Plan, PlanFactory]):
    """Executor for planning layer tasks."""
    
    # Required class attributes
    _strategy_type = PlanStrategy
    _default_strategy = PlanStrategy.DEFAULT
    graph_class = Plan
    _factory_class = PlanFactory
    _depth = 1

    def __init__(self, 
                 strategy: PlanStrategy = PlanStrategy.DEFAULT,
                 lower_executor: Optional['BaseExecutor'] = None):
        """Initialize the plan executor.
        
        Args:
            planning_strategy: Strategy for plan execution
            reasoning_strategy: Strategy for reasoning execution
        """
        if lower_executor is None:
            lower_executor = Reasoner(ReasoningStrategy.DEFAULT)
        super().__init__(strategy, lower_executor)
    