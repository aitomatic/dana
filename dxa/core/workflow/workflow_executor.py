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
from ..workflow import Workflow
from ...common.graph import NodeType

class WorkflowStrategy(Enum):
    """Workflow execution strategies."""
    DEFAULT = "DEFAULT"      # Graph-based workflow
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONDITIONAL = "CONDITIONAL"

class WorkflowExecutor(Executor):
    """Executes workflow graphs."""

    def __init__(self, plan_executor: PlanExecutor, strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT):
        super().__init__()
        self.plan_executor = plan_executor
        self.strategy = strategy

    async def execute_workflow(self, workflow: Workflow, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute given workflow graph."""
        context.current_workflow = workflow
        self.graph = cast(ExecutionGraph, workflow)
        return await super().execute(workflow, context)

    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute node based on its type."""

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
        workflow = Workflow(objective)
        context.current_workflow = workflow
        return cast(ExecutionGraph, workflow)
