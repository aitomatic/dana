"""Plan executor implementation."""

from typing import Optional
from ..executor import Executor
from .plan import Plan
from .plan_strategy import PlanStrategy
from ..reasoning import ReasoningExecutor, ReasoningStrategy
from .plan_factory import PlanFactory

class PlanExecutor(Executor[PlanStrategy, Plan, PlanFactory]):
    """Executor for planning layer tasks."""
    
    # Required class attributes
    _strategy_type = PlanStrategy
    _default_strategy = PlanStrategy.DEFAULT
    graph_class = Plan
    _factory_class = PlanFactory
    _depth = 1

    def __init__(self, 
                 strategy: PlanStrategy = PlanStrategy.DEFAULT,
                 lower_executor: Optional['Executor'] = None):
        """Initialize the plan executor.
        
        Args:
            planning_strategy: Strategy for plan execution
            reasoning_strategy: Strategy for reasoning execution
        """
        if lower_executor is None:
            lower_executor = ReasoningExecutor(ReasoningStrategy.DEFAULT)
        super().__init__(strategy, lower_executor)
    