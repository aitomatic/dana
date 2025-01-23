"""Plan executor implementation."""

from enum import StrEnum
from typing import List, cast, Optional, TYPE_CHECKING

from ..execution_context import ExecutionContext
from ..execution_types import (
    ExecutionNode,
    ExecutionSignal,
    Objective,
    ExecutionEdge
)
from ..execution_graph import ExecutionGraph
from ..executor import Executor
from .plan import Plan
from ..workflow.workflow import Workflow
from ....common.graph import NodeType

if TYPE_CHECKING:
    from ..reasoning import ReasoningExecutor

class PlanningStrategy(StrEnum):
    """Planning strategies."""
    DEFAULT = "DEFAULT"        # same as WORKFLOW_IS_PLAN
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"  # Exact structural copy with cursor sync
    COMPLETE = "COMPLETE"    # Whole workflow
    DYNAMIC = "DYNAMIC"      # Adaptive planning

class PlanExecutor(Executor):
    """Executes plans using planning strategies."""

    def __init__(self, reasoning_executor: 'ReasoningExecutor', strategy: PlanningStrategy = PlanningStrategy.DEFAULT):
        super().__init__()
        self.reasoning_executor = reasoning_executor
        self._strategy = strategy

    @property
    def strategy(self) -> PlanningStrategy:
        """Get workflow strategy."""
        if self._strategy == PlanningStrategy.DEFAULT:
            self._strategy = PlanningStrategy.WORKFLOW_IS_PLAN
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: PlanningStrategy):
        """Set workflow strategy."""
        if strategy == PlanningStrategy.DEFAULT:
            strategy = PlanningStrategy.WORKFLOW_IS_PLAN
        self._strategy = strategy

    async def execute_node(self, node: ExecutionNode,
                           context: ExecutionContext,
                           prev_signals: List[ExecutionSignal],
                           upper_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute a plan node using reasoning executor."""

        # TODO: use upper_signals somehow?

        # Safety: make sure our graph is set
        if self.graph is None and context.current_plan:
            self.graph = context.current_plan

        if context.current_plan is None and self.graph:
            context.current_plan = cast(Plan, self.graph)

        # Get the workflow from context
        workflow = cast(Workflow, context.current_workflow)

        # Update workflow cursor if using COPY_WORKFLOW strategy
        if self.strategy == PlanningStrategy.WORKFLOW_IS_PLAN:
            workflow.update_cursor(node.node_id)  # Uses DirectedGraph's method

        if node.node_type in [NodeType.START, NodeType.END]:
            return []   # Start and end nodes just initialize/terminate flow

        # Execute the node
        assert self.graph is not None
        signals = await self.reasoning_executor.execute(upper_graph=self.graph,
                                                        context=context,
                                                        # Pass my prev_signals down to reasoning executor
                                                        upper_signals=prev_signals
                                                        )

        return signals

    def _create_graph(self,
                      upper_graph: ExecutionGraph,
                      objective: Optional[Objective] = None,
                      context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create this layer's graph from the upper layer's graph."""
        plan = self._create_plan(cast(Workflow, upper_graph), objective)
        assert context is not None
        context.current_plan = plan
        return cast(ExecutionGraph, plan)

    def _create_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create plan based on selected strategy."""
        objective = objective or workflow.objective

        if self.strategy == PlanningStrategy.DEFAULT:
            return self._create_direct_plan(workflow, objective)
        if self.strategy == PlanningStrategy.COMPLETE:
            return self._create_complete_plan(workflow, objective)
        if self.strategy == PlanningStrategy.DYNAMIC:
            return self._create_dynamic_plan(workflow, objective)
        if self.strategy == PlanningStrategy.WORKFLOW_IS_PLAN:
            return self._create_follow_workflow_plan(workflow, objective)
        raise ValueError(f"Unknown strategy: {self.strategy}")

    def _create_direct_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create direct 1:1 plan from current task."""
        # Use the current node from workflow execution
        current_node = workflow.get_current_node()
        if not current_node:
            raise ValueError("No current node in workflow")

        assert objective is not None
        plan = self._create_execution_graph([
            ExecutionNode(
                node_id="DIRECT_STEP",
                node_type=NodeType.TASK,
                description=objective.original
            )
        ])
        plan.objective = objective
        return cast(Plan, plan)

    def _create_complete_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create plan for complete workflow."""
        plan = Plan(objective)
        for node in workflow.nodes.values():
            if node.node_type == NodeType.TASK:
                plan.add_step(
                    step_id=f"step_{node.node_id}",
                    description=node.description
                )
        return plan

    def _create_dynamic_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create adaptive plan based on context."""
        # For now, same as direct
        return self._create_direct_plan(workflow, objective)

    def _create_follow_workflow_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create exact structural copy of workflow."""
        plan = Plan(objective or workflow.objective)

        # Copy nodes with same IDs to maintain cursor sync
        for node_id, node in workflow.nodes.items():
            plan.add_node(ExecutionNode(
                node_id=node_id,  # Keep same IDs
                node_type=node.node_type,
                description=node.description
            ))

        # Copy edges to maintain structure
        for edge in workflow.edges:
            plan.add_edge(ExecutionEdge(edge.source, edge.target))

        return plan
