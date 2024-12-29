"""Plan executor implementation."""

from enum import Enum
from typing import List, cast, Optional
from ..execution import Executor, ExecutionNode, ExecutionSignal, ExecutionContext
from ..execution import Objective
from .plan import Plan
from ..workflow import Workflow
from ..execution import ExecutionGraph
from ...common.graph import NodeType

class PlanningStrategy(Enum):
    """Planning strategies."""
    DIRECT = "DIRECT"        # 1:1 mapping
    COMPLETE = "COMPLETE"    # Whole workflow
    DYNAMIC = "DYNAMIC"      # Adaptive planning

class PlanExecutor(Executor):
    """Executes plans using planning strategies."""

    def __init__(self, reasoning_executor, strategy: PlanningStrategy = PlanningStrategy.DIRECT):
        super().__init__()
        self.reasoning_executor = reasoning_executor
        self.strategy = strategy

    async def execute(self, upper_graph: ExecutionGraph, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute using planning strategy."""
        # Create plan based on strategy
        workflow = cast(Workflow, upper_graph)
        # For now, use workflow objective
        objective = workflow.objective
        plan = self._create_plan(workflow, objective)
        
        # Update context with new plan
        context.current_plan = plan
        self.graph = cast(ExecutionGraph, plan)
        
        # Execute plan through base executor
        return await super().execute(workflow, context)

    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a plan node using reasoning executor."""
        if node.node_type == NodeType.START or node.node_type == NodeType.END:
            return []   # Start and end nodes just initialize/terminate flow
        
        return await self.reasoning_executor.execute(self.graph, context)

    def _create_graph(self, upper_graph: ExecutionGraph, objective: Optional[Objective] = None) -> ExecutionGraph:
        """Create this layer's graph from the upper layer's graph."""
        plan = self._create_plan(cast(Workflow, upper_graph), objective)
        return cast(ExecutionGraph, plan)

    def _create_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create plan based on selected strategy."""
        objective = objective or workflow.objective

        if self.strategy == PlanningStrategy.DIRECT:
            return self._create_direct_plan(workflow, objective)
        elif self.strategy == PlanningStrategy.COMPLETE:
            return self._create_complete_plan(workflow, objective)
        elif self.strategy == PlanningStrategy.DYNAMIC:
            return self._create_dynamic_plan(workflow, objective)
        else:
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
