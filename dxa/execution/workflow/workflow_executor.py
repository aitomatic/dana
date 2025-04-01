"""Workflow executor implementation."""

from typing import List, Optional

from dxa.execution.execution_context import ExecutionContext
from dxa.execution.execution_graph import ExecutionGraph
from dxa.execution.execution_types import ExecutionSignal
from ..executor import Executor
from .workflow import Workflow
from .workflow_strategy import WorkflowStrategy
from .workflow_factory import WorkflowFactory
from ..planning import PlanExecutor, PlanStrategy

class WorkflowExecutor(Executor[WorkflowStrategy, Workflow, WorkflowFactory]):
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
                 lower_executor: Optional['Executor'] = None):
        """Initialize the workflow executor.
        
        Args:
            workflow_strategy: Strategy for workflow execution
            planning_strategy: Strategy for plan execution
        """
        if lower_executor is None:
            lower_executor = PlanExecutor(PlanStrategy.DEFAULT)
        super().__init__(strategy, lower_executor)
    
    async def execute_workflow(
        self,
        workflow: ExecutionGraph,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow graph with optimized three-layer pattern.
        
        Args:
            workflow: The workflow graph to execute
            context: Execution context
            prev_signals: Previous execution signals
            upper_signals: Signals from upper layer
            lower_signals: Signals from lower layer
            
        Returns:
            List of execution signals
        """
        # Set up execution context
        self.workflow = workflow
        self.context = context
        
        # Initialize results manager with workflow
        start_node = workflow.get_start_node()
        assert start_node is not None, "Workflow must have a start node"
        # self.results.set_current_plan(start_node.node_id)
        
        # Execute the graph
        return await self.execute(
            workflow,
            context,
            prev_signals,
            upper_signals,
            lower_signals
        )