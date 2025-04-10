"""Workflow executor implementation."""

from typing import Optional
from ..base_executor import BaseExecutor
from .workflow import Workflow
from .workflow_strategy import WorkflowStrategy
from .workflow_factory import WorkflowFactory
from ..planning import PlanExecutor, PlanStrategy

class WorkflowExecutor(BaseExecutor[WorkflowStrategy, Workflow, WorkflowFactory]):
    """Executor for workflow layer tasks.
    
    This executor handles the workflow layer of execution, which is
    responsible for executing individual workflow tasks.
    """
    
    # Required class attributes
    _strategy_type = WorkflowStrategy
    _default_strategy = WorkflowStrategy.DEFAULT
    graph_class = Workflow
    _factory_class = WorkflowFactory
    _depth = 0

    def __init__(self, 
                 strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT,
                 lower_executor: Optional['BaseExecutor'] = None):
        """Initialize the workflow executor.
        
        Args:
            workflow_strategy: Strategy for workflow execution
            planning_strategy: Strategy for plan execution
        """
        if lower_executor is None:
            lower_executor = PlanExecutor(PlanStrategy.DEFAULT)
        super().__init__(strategy, lower_executor)
        