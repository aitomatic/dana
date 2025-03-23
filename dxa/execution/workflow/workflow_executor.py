"""Workflow executor implementation."""

from typing import List, Optional, Dict, Any, cast

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal
from .workflow_strategy import WorkflowStrategy
from ..planning.plan_executor import PlanExecutor
from ..planning.plan import Plan

class WorkflowExecutor(Executor[WorkflowStrategy]):
    """Executes workflows by delegating to a plan executor.
    
    The WorkflowExecutor is responsible for executing workflow graphs,
    which represent high-level execution flows. It delegates the actual
    execution of tasks to a PlanExecutor.
    """
    
    @property
    def layer(self) -> str:
        """Get the execution layer name."""
        return "workflow"
    
    @property
    def strategy_class(self) -> type[WorkflowStrategy]:
        """Get the strategy class for this executor."""
        return WorkflowStrategy
    
    @property
    def default_strategy(self) -> WorkflowStrategy:
        """Get the default strategy for this executor."""
        return WorkflowStrategy.DEFAULT
    
    def __init__(
        self, 
        plan_executor: PlanExecutor, 
        strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT
    ):
        """Initialize the workflow executor.
        
        Args:
            plan_executor: Plan executor to use for executing tasks
            strategy: Workflow execution strategy
        """
        super().__init__(depth=0)
        self.lower_executor = plan_executor
        self.strategy = strategy
    
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build workflow context for node execution.
        
        Args:
            node: Node to execute
            prev_signals: Signals from previous node execution
            
        Returns:
            Workflow context dictionary
        """
        context = {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "description": node.description,
            "metadata": node.metadata or {}
        }
        
        # Add previous outputs if available
        if prev_signals:
            context["previous_outputs"] = {
                signal.content.get("node"): signal.content.get("output")
                for signal in prev_signals
                if signal.type == "output"
            }
        
        return context
    
    async def _execute_next_layer(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute the plan layer for the given node.
        
        Args:
            node: Node to execute
            context: Execution context
            
        Returns:
            List of execution signals
        """
        if not self.graph:
            raise RuntimeError("No graph set for workflow execution")
            
        if not self.lower_executor:
            raise RuntimeError("No plan executor set")
            
        # Create plan graph from workflow node
        plan_graph = self.lower_executor.create_graph_from_node(
            upper_node=node,
            upper_graph=self.graph,
            objective=self.graph.objective if self.graph else None,
            context=context
        )
        
        # Cast to Plan type
        plan = cast(Plan, plan_graph)
        
        # Set plan graph in context
        context.current_plan = plan
        
        # Execute plan graph
        return await self.lower_executor.execute_graph(plan, context)