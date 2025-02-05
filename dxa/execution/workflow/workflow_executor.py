"""Workflow executor implementation."""

from enum import Enum
from typing import List, cast, Optional, TYPE_CHECKING
from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, Objective
from ..execution_graph import ExecutionGraph
from ..executor import Executor
from .workflow import Workflow
from .workflow_factory import WorkflowFactory
from ...common.graph import NodeType

if TYPE_CHECKING:
    from ..planning.plan_executor import PlanExecutor

class WorkflowStrategy(Enum):
    """Workflow execution strategies."""
    DEFAULT = "DEFAULT"      # same as WORKFLOW_IS_PLAN
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"

class WorkflowExecutor(Executor):
    """Executes workflow graphs."""

    def __init__(self, plan_executor: 'PlanExecutor', strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT):
        super().__init__(depth=1)
        self.plan_executor = plan_executor
        self._strategy = strategy
        self.layer = "workflow"
        self._configure_logger()

    @property
    def strategy(self) -> WorkflowStrategy:
        """Get workflow strategy."""
        if self._strategy == WorkflowStrategy.DEFAULT:
            self._strategy = WorkflowStrategy.WORKFLOW_IS_PLAN
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: WorkflowStrategy):
        """Set workflow strategy."""
        if strategy == WorkflowStrategy.DEFAULT:
            strategy = WorkflowStrategy.WORKFLOW_IS_PLAN
        self._strategy = strategy

    async def execute_workflow(self, workflow: Workflow, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute given workflow graph."""
        context.current_workflow = workflow
        self.graph = cast(ExecutionGraph, workflow)
        return await self.execute(upper_graph=cast(ExecutionGraph, None), context=context, upper_signals=None)

    async def execute(self,
                      upper_graph: ExecutionGraph,
                      context: ExecutionContext,
                      upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow graph. Upper signals are not used in the workflow layer."""
        if self.strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
            # Go directly to plan execution, via the START node
            assert self.graph is not None
            return await self.plan_executor.execute(self.graph, context, None)

        return await super().execute(upper_graph=upper_graph, context=context, upper_signals=None)

    async def execute_node(self, node: ExecutionNode,
                           context: ExecutionContext,
                           prev_signals: Optional[List[ExecutionSignal]] = None,
                           upper_signals: Optional[List[ExecutionSignal]] = None,
                           lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute node based on its type and strategy.
        Upper signals are not used in the workflow layer."""

        # Safety: make sure our graph is set
        if self.graph is None and context.current_workflow:
            self.graph = context.current_workflow

        if context.current_workflow is None and self.graph:
            context.current_workflow = cast(Workflow, self.graph)

        if node.node_type in [NodeType.START, NodeType.END]:
            return []  # Start and end nodes just initialize/terminate flow

        if node.node_type == NodeType.TASK:
            assert self.graph is not None
            # Pass current cursor position
            return await self.plan_executor.execute(
                upper_graph=self.graph,
                context=context,
                upper_signals=prev_signals  # Pass my prev_signals down to plan executor
            )

        self.logger.debug(
            "Processing workflow node",
            node_id=node.node_id,
            node_type=node.node_type
        )

        return []

    def _create_graph(self, upper_graph: ExecutionGraph, objective: Optional[Objective] = None,
                       context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create workflow graph from objective. At the Worflow layer, there is no upper graph."""
        workflow = WorkflowFactory.create_minimal_workflow(objective)
        assert context is not None
        context.current_workflow = workflow
        return cast(ExecutionGraph, workflow)
