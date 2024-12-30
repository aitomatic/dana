"""Workflow executor implementation."""

from enum import Enum
from typing import List, cast, Optional
from ..execution import (
    Executor,
    ExecutionGraph,
    ExecutionNode,
    ExecutionSignal,
    ExecutionContext,
    Objective,
)
from ..planning import PlanExecutor
from ..workflow import WorkflowFactory, Workflow
from ...common.graph import NodeType

class WorkflowStrategy(Enum):
    """Workflow execution strategies."""
    DEFAULT = "DEFAULT"      # same as WORKFLOW_IS_PLAN
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"

class WorkflowExecutor(Executor):
    """Executes workflow graphs."""

    def __init__(self, plan_executor: PlanExecutor, strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT):
        super().__init__()
        self.plan_executor = plan_executor
        self._strategy = strategy
    
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
        return await self.execute(None, context)
    
    async def execute(self, upper_graph: ExecutionGraph, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute workflow graph."""
        if self.strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
            # Go directly to plan execution, via the START node
            return await self.plan_executor.execute(self.graph, context)

        return await super().execute(upper_graph, context)

    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute node based on its type."""

        # Safety: make sure our graph is set
        if self.graph is None and context.current_workflow:
            self.graph = context.current_workflow
        
        if context.current_workflow is None and self.graph:
            context.current_workflow = self.graph

        if node.node_type == NodeType.START or node.node_type == NodeType.END:
            return []  # Start and end nodes just initialize/terminate flow
            
        elif node.node_type == NodeType.TASK:
            assert self.graph is not None
            # Pass current cursor position
            return await self.plan_executor.execute(
                upper_graph=self.graph, 
                context=context
            )
            
        return [] 

    def _create_graph(self, upper_graph: ExecutionGraph, objective: Optional[Objective] = None, 
                       context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create workflow graph from objective. At the Worflow layer, there is no upper graph."""
        workflow = WorkflowFactory.create_minimal_workflow(objective)
        context.current_workflow = workflow
        return cast(ExecutionGraph, workflow)
