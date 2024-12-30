"""Plan executor implementation."""

from enum import Enum
from typing import List, cast, Optional
from ..execution import Executor, ExecutionNode, ExecutionSignal, ExecutionContext
from ..execution import Objective
from .plan import Plan
from ..workflow import Workflow
from ..execution import ExecutionGraph, ExecutionEdge
from ...common.graph import NodeType

class PlanningStrategy(Enum):
    """Planning strategies."""
    DIRECT = "DIRECT"        # 1:1 mapping
    COMPLETE = "COMPLETE"    # Whole workflow
    DYNAMIC = "DYNAMIC"      # Adaptive planning
    FOLLOW_WORKFLOW = "FOLLOW_WORKFLOW"  # Exact structural copy with cursor sync

class PlanExecutor(Executor):
    """Executes plans using planning strategies."""

    def __init__(self, reasoning_executor, strategy: PlanningStrategy = PlanningStrategy.DIRECT):
        super().__init__()
        self.reasoning_executor = reasoning_executor
        self.strategy = strategy

    async def execute_node(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a plan node using reasoning executor."""
        if node.node_type == NodeType.START or node.node_type == NodeType.END:
            return []   # Start and end nodes just initialize/terminate flow
        
        # Get the workflow from context
        workflow = cast(Workflow, context.current_workflow)
        
        # Execute the node
        signals = await self.reasoning_executor.execute(self.graph, context)
        
        # Update workflow cursor if using COPY_WORKFLOW strategy
        if self.strategy == PlanningStrategy.FOLLOW_WORKFLOW:
            workflow.update_cursor(node.node_id)  # Uses DirectedGraph's method
        
        return signals

    def _create_graph(self, 
                      upper_graph: ExecutionGraph, 
                      objective: Optional[Objective] = None, 
                      context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create this layer's graph from the upper layer's graph."""
        plan = self._create_plan(cast(Workflow, upper_graph), objective)
        context.current_plan = plan
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
        elif self.strategy == PlanningStrategy.FOLLOW_WORKFLOW:
            return self._create_follow_workflow_plan(workflow, objective)
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
