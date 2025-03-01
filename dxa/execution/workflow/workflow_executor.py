"""Workflow executor implementation."""

from enum import Enum
from typing import List, cast, Optional, TYPE_CHECKING

from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, Objective
from ..execution_graph import ExecutionGraph
from ..executor import Executor
from .workflow import Workflow
from ...common.graph import NodeType
from ...common.utils.text_processor import TextProcessor

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
        self.parse_by_key = TextProcessor().parse_by_key

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

    async def execute(self, upper_graph: Optional[ExecutionGraph], 
                      context: ExecutionContext,
                      upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow graph. Upper signals are not used in the workflow layer."""
        # Safety: make sure our graph is set
        if self.graph is None and context.current_workflow:
            self.graph = context.current_workflow

        # Set current plan and reasoning in context
        context.current_plan = self.graph
        context.current_reasoning = self.graph
        
        # Select execution strategy based on workflow metadata
        strategy_name = self.graph.metadata.get("strategy", self.strategy.value)
        try:
            strategy = WorkflowStrategy(strategy_name)
        except ValueError:
            self.logger.warning(f"Unknown workflow strategy: {strategy_name}, using default")
            strategy = self.strategy
            
        self.logger.info(f"Executing workflow with strategy: {strategy.name}")
            
        # Execute based on strategy
        if strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
            return await self._execute_workflow_as_plan(context, upper_signals)
        elif strategy == WorkflowStrategy.SEQUENTIAL:
            return await self._execute_sequential(context, upper_signals)
        elif strategy == WorkflowStrategy.PARALLEL:
            return await self._execute_parallel(context, upper_signals)
        elif strategy == WorkflowStrategy.CONDITIONAL:
            return await self._execute_conditional(context, upper_signals)
        else:
            self.logger.error(f"Unsupported workflow strategy: {strategy.name}")
            raise ValueError(f"Unsupported workflow strategy: {strategy.name}")

    async def _execute_workflow_as_plan(self, context: ExecutionContext, 
                                       upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow by treating it as a plan."""
        # Go directly to plan execution, via the START node
        assert self.graph is not None
        start_node = self.graph.get_node_by_id("START")
        if not start_node:
            self.logger.error("No START node found in workflow graph")
            raise ValueError("No START node found in workflow graph")
            
        return await super().execute(upper_graph=self.graph, context=context, upper_signals=upper_signals)

    async def _execute_sequential(self, context: ExecutionContext,
                                 upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow nodes in sequence."""
        assert self.graph is not None
        all_signals = []
        
        # Start from the START node
        current_node_id = "START"
        visited = set()
        
        while current_node_id != "END":
            # Prevent infinite loops
            if current_node_id in visited:
                self.logger.error(f"Cycle detected at node {current_node_id}")
                raise ValueError(f"Cycle detected at node {current_node_id}")
                
            visited.add(current_node_id)
            
            # Get the current node
            current_node = self.graph.get_node_by_id(current_node_id)
            if not current_node:
                self.logger.error(f"Node {current_node_id} not found in workflow graph")
                raise ValueError(f"Node {current_node_id} not found in workflow graph")
                
            # Execute the node
            if current_node.node_type == NodeType.TASK:
                self.logger.info(f"Executing node: {current_node_id}")
                signals = await self.execute_node(current_node, context, all_signals, upper_signals)
                all_signals.extend(signals)
            
            # Find the next node
            outgoing_edges = self.graph.get_outgoing_edges(current_node_id)
            if not outgoing_edges:
                self.logger.error(f"No outgoing edges from node {current_node_id}")
                raise ValueError(f"No outgoing edges from node {current_node_id}")
                
            # For sequential, just take the first edge
            current_node_id = outgoing_edges[0].target
            
        return all_signals

    async def _execute_parallel(self, context: ExecutionContext,
                               upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow nodes in parallel."""
        # This is a placeholder for future implementation
        self.logger.warning("Parallel execution not yet implemented, falling back to sequential")
        return await self._execute_sequential(context, upper_signals)

    async def _execute_conditional(self, context: ExecutionContext,
                                  upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute workflow with conditional branching."""
        # This is a placeholder for future implementation
        self.logger.warning("Conditional execution not yet implemented, falling back to sequential")
        return await self._execute_sequential(context, upper_signals)

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
            extra={
                'node_id': node.node_id,
                'node_type': node.node_type
            }
        )

        return []

    def _create_graph(self, upper_graph: ExecutionGraph, objective: Optional[Objective] = None,
                       context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create workflow graph from objective. At the Workflow layer, there is no upper graph."""
        from .workflow_factory import WorkflowFactory
        workflow = WorkflowFactory.create_minimal_workflow(objective)
        assert context is not None
        context.current_workflow = workflow
        return cast(ExecutionGraph, workflow)
