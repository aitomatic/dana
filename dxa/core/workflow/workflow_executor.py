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

    def _create_graph(self, upper_graph: ExecutionGraph, objective: Optional[Objective] = None) -> ExecutionGraph:
        """Create workflow graph from objective. At the Worflow layer, there is no upper graph."""
        workflow = self.create_minimal_workflow(objective)
        return cast(ExecutionGraph, workflow)

    def create_minimal_workflow(self, objective: Optional[Objective] = None) -> Workflow:
        """Create workflow graph from objective."""
        # For simple QA, create linear workflow
        workflow = Workflow()
        workflow.objective = objective

        # Add START node
        workflow.add_node(ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Begin workflow"
        ))
        
        # Add question task
        workflow.add_node(ExecutionNode(
            node_id="ANSWER_QUESTION",
            node_type=NodeType.TASK,
            description=str(objective)
        ))
        workflow.add_transition("START", "ANSWER_QUESTION")
        
        # Add END node
        workflow.add_node(ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End workflow"
        ))
        workflow.add_transition("ANSWER_QUESTION", "END")
        
        return workflow 