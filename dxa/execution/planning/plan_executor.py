"""Plan executor implementation."""

from enum import Enum
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
from ...common.graph import NodeType
from ..reasoning.reasoning_factory import ReasoningFactory

if TYPE_CHECKING:
    from ..reasoning import ReasoningExecutor

class PlanStrategy(Enum):
    """Planning strategies."""
    DEFAULT = "DEFAULT"        # same as WORKFLOW_IS_PLAN
    WORKFLOW_IS_PLAN = "WORKFLOW_IS_PLAN"  # Exact structural copy with cursor sync
    COMPLETE = "COMPLETE"    # Whole workflow
    DYNAMIC = "DYNAMIC"      # Adaptive planning
    PROSEA = "PROSEA"        # PROSEA planning

class PlanExecutor(Executor):
    """Executes plans using planning strategies."""

    def __init__(self, reasoning_executor: 'ReasoningExecutor', strategy: PlanStrategy = PlanStrategy.DEFAULT):
        super().__init__(depth=2)
        self.reasoning_executor = reasoning_executor
        self._strategy = strategy
        self.layer = "plan"
        self._configure_logger()

    @property
    def strategy(self) -> PlanStrategy:
        """Get workflow strategy."""
        if self._strategy == PlanStrategy.DEFAULT:
            self._strategy = PlanStrategy.WORKFLOW_IS_PLAN
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: PlanStrategy):
        """Set workflow strategy."""
        if strategy == PlanStrategy.DEFAULT:
            strategy = PlanStrategy.WORKFLOW_IS_PLAN
        self._strategy = strategy

    async def execute_node(self, node: ExecutionNode,
                           context: ExecutionContext,
                           validation_node: Optional[ExecutionNode] = None,
                           original_problem: Optional[str] = None,
                           agent_role: Optional[str] = None,
                           prev_signals: Optional[List[ExecutionSignal]] = None,
                           upper_signals: Optional[List[ExecutionSignal]] = None,
                           lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute a plan node using reasoning executor."""

        # Safety: make sure our graph is set
        if self.graph is None and context.current_plan:
            self.graph = context.current_plan
            
        if context.current_plan is None and self.graph:
            context.current_plan = cast(Plan, self.graph)

        # Get the workflow from context
        workflow = cast(Workflow, context.current_workflow)

        # Update workflow cursor if using COPY_WORKFLOW strategy
        if self.strategy == PlanStrategy.WORKFLOW_IS_PLAN:
            workflow.update_cursor(node.node_id)  # Uses DirectedGraph's method

        if node.node_type in [NodeType.START, NodeType.END]:
            return []   # Start and end nodes just initialize/terminate flow
            
        # Select appropriate reasoning strategy for this node
        if self.reasoning_executor.strategy == "AUTO":
            # Use ReasoningFactory to select appropriate strategy
            selected_strategy = ReasoningFactory.create_reasoning_strategy(node, context)
            # Store original strategy to restore later
            original_strategy = self.reasoning_executor.strategy
            # Set selected strategy for this node
            self.reasoning_executor.strategy = selected_strategy
            
            # Execute with selected strategy
            signals = await self.reasoning_executor.execute_node(
                node=node, 
                context=context, 
                validation_node=validation_node, 
                original_problem=original_problem, 
                agent_role=agent_role, 
                prev_signals=prev_signals, 
                upper_signals=upper_signals, 
                lower_signals=lower_signals
            )
            
            # Restore original strategy
            self.reasoning_executor.strategy = original_strategy
            return signals
        else:
            # Use the configured strategy
            return await self.reasoning_executor.execute_node(
                node=node, 
                context=context, 
                validation_node=validation_node, 
                original_problem=original_problem, 
                agent_role=agent_role, 
                prev_signals=prev_signals, 
                upper_signals=upper_signals, 
                lower_signals=lower_signals
            )
        
    def _create_graph(self,
                      upper_graph: ExecutionGraph,
                      objective: Optional[Objective] = None,
                      context: Optional[ExecutionContext] = None) -> ExecutionGraph:
        """Create this layer's graph from the upper layer's graph."""
        plan = self._create_plan(cast(Workflow, upper_graph), objective)
        assert context is not None
        context.current_plan = plan
        assert upper_graph.objective is not None
        self.logger.info(
            "Plan created", 
            extra={
                'strategy': self.strategy.value,
                'steps': len(plan.nodes),
                'source_workflow': upper_graph.objective.original[:50] + "..."
            }
        )
        return cast(ExecutionGraph, plan)

    def _create_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create plan based on selected strategy."""
        objective = objective or workflow.objective

        if self.strategy == PlanStrategy.DEFAULT:
            return self._create_direct_plan(workflow, objective)
        if self.strategy == PlanStrategy.COMPLETE:
            return self._create_complete_plan(workflow, objective)
        if self.strategy == PlanStrategy.DYNAMIC:
            return self._create_dynamic_plan(workflow, objective)
        if self.strategy == PlanStrategy.WORKFLOW_IS_PLAN:
            return self._create_follow_workflow_plan(workflow, objective)
        if self.strategy == PlanStrategy.PROSEA:
            return self._create_prosea_plan(workflow, objective)
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
            # Copy node metadata including reasoning strategy
            metadata = node.metadata.copy() if node.metadata else {}
            
            # If no reasoning strategy specified, set AUTO as default
            if node.node_type == NodeType.TASK and "reasoning_strategy" not in metadata:
                metadata["reasoning_strategy"] = "AUTO"
                
            plan.add_node(ExecutionNode(
                node_id=node_id,  # Keep same IDs
                node_type=node.node_type,
                description=node.description,
                metadata=metadata
            ))

        # Copy edges to maintain structure
        for edge in workflow.edges:
            plan.add_edge(ExecutionEdge(edge.source, edge.target))

        return plan
        
    def _create_prosea_plan(self, workflow: Workflow, objective: Optional[Objective] = None) -> Plan:
        """Create a plan for PROSEA workflow."""
        plan = Plan(objective or workflow.objective)
        
        # Copy nodes with same IDs to maintain cursor sync
        for node_id, node in workflow.nodes.items():
            # Copy node metadata including reasoning strategy
            metadata = node.metadata.copy() if node.metadata else {}
            
            # Set specific reasoning strategies for PROSEA nodes
            if node.node_id == "ANALYZE":
                metadata["reasoning_strategy"] = "DIRECT"
            elif node.node_id == "PLANNING":
                metadata["reasoning_strategy"] = "DIRECT"
            elif node.node_id == "FINALIZE_ANSWER":
                metadata["reasoning_strategy"] = "DIRECT"
            elif node.node_type == NodeType.TASK and "reasoning_strategy" not in metadata:
                metadata["reasoning_strategy"] = "AUTO"
                
            plan.add_node(ExecutionNode(
                node_id=node_id,  # Keep same IDs
                node_type=node.node_type,
                description=node.description,
                metadata=metadata
            ))

        # Copy edges to maintain structure
        for edge in workflow.edges:
            plan.add_edge(ExecutionEdge(edge.source, edge.target))
            
        return plan

    async def execute_node_prosea(self, node: ExecutionNode, context: ExecutionContext,
                                  validation_node: Optional[ExecutionNode] = None,
                                  prev_signals: Optional[List[ExecutionSignal]] = None,
                                  upper_signals: Optional[List[ExecutionSignal]] = None,
                                  lower_signals: Optional[List[ExecutionSignal]] = None) -> List[ExecutionSignal]:
        """Execute a plan node using reasoning executor."""
        
        response = await self.reasoning_executor.execute_node(node, context, validation_node, prev_signals, upper_signals, lower_signals)
        
    async def _execute_step(self, step: ExecutionNode, context: ExecutionContext):
        self.logger.debug(
            "Executing plan step",
            step=getattr(context.agent_state, 'current_step_index', 0),
            node_id=step.node_id
        )
