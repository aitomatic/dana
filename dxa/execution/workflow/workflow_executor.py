"""Workflow executor implementation."""

from typing import List, Optional, Dict, Any

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal
from .workflow_strategy import WorkflowStrategy
from ..planning.plan_executor import PlanExecutor
from ..planning.plan_strategy import PlanStrategy
from ..reasoning.reasoning_executor import ReasoningExecutor
from ..reasoning.reasoning_strategy import ReasoningStrategy
from .workflow import Workflow
from ..execution_types import Objective

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
        workflow_strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT,
        planning_strategy: PlanStrategy = PlanStrategy.DEFAULT,
        reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT
    ):
        """Initialize the workflow executor.
        
        Args:
            plan_executor: Plan executor to use for executing tasks
            strategy: Workflow execution strategy
        """
        super().__init__(depth=0)
        self.strategy = workflow_strategy
        self.lower_executor = PlanExecutor(strategy=planning_strategy)
        self.lower_executor.lower_executor = ReasoningExecutor(strategy=reasoning_strategy)
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow graph.
        
        This is the main entry point for executing a workflow. It sets up
        the execution context and delegates to the common graph execution
        logic.
        
        Args:
            workflow: Workflow graph to execute
            context: Execution context
            prev_signals: Signals from previous execution
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals
        """
        # Set the workflow graph
        self.graph = workflow
        
        # Set the workflow in context
        context.current_workflow = workflow
        
        # Execute the graph using common logic
        return await self.execute_graph(
            workflow,
            context,
            prev_signals,
            upper_signals,
            lower_signals
        )
    
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
    
    def create_graph_from_node(
            self,
            upper_node: ExecutionNode,
            upper_graph: ExecutionGraph,
            objective: Optional[Objective] = None,
            context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """This is never called since there is no upper layer."""
        return ExecutionGraph()
