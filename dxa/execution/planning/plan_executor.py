"""Plan executor implementation."""

from typing import List, Optional, Dict, Any

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal, Objective
from .plan import Plan
from .plan_strategy import PlanStrategy
from ..reasoning.reasoning_executor import ReasoningExecutor


class PlanExecutor(Executor[PlanStrategy, Plan]):
    """Executes plans by delegating to a reasoning executor.
    
    The PlanExecutor is responsible for executing plan graphs,
    which represent mid-level execution flows. It delegates the actual
    reasoning tasks to a ReasoningExecutor.
    """
    
    # Class attributes for layer configuration
    _default_strategy_value = PlanStrategy.DEFAULT
    _depth = 1
    
    def __init__(
        self, 
        strategy: PlanStrategy = PlanStrategy.DEFAULT,
        lower_executor: Optional['ReasoningExecutor'] = None
    ):
        """Initialize plan executor.
        
        Args:
            strategy: Plan execution strategy
            lower_executor: Optional reasoning executor
        """
        super().__init__(strategy=strategy, lower_executor=lower_executor)
    
    def create_graph_from_upper_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> Optional[Plan]:
        """Create a plan execution graph from a node in the workflow.
        
        This method extends the base implementation to handle planning-specific
        graph creation strategies:
        1. DEFAULT: Direct plan following workflow structure
        2. DYNAMIC: Adaptive plan that evolves during execution
        3. INCREMENTAL: Plan that only looks ahead a few steps
        
        Args:
            upper_node: Node from the workflow layer
            upper_graph: Graph from the workflow layer
            objective: Execution objective
            context: Execution context
            
        Returns:
            Plan execution graph
        """
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
        
        # Get the workflow graph
        workflow = upper_graph
        if not workflow:
            # Create a minimal plan if no workflow is available
            return self._create_minimal_graph(upper_node, objective)
        
        # Create a plan based on the strategy
        if self.strategy == PlanStrategy.DEFAULT:
            # Direct execution - create a minimal plan that follows the workflow structure
            return self._create_direct_graph(workflow, objective, upper_node)
        elif self.strategy == PlanStrategy.DYNAMIC:
            return self._create_dynamic_plan(workflow, objective, upper_node)
        elif self.strategy == PlanStrategy.INCREMENTAL:
            return self._create_incremental_plan(workflow, objective, upper_node)
        else:
            # Default to direct plan
            return self._create_direct_graph(workflow, objective, upper_node)
    
    def _create_dynamic_plan(
        self, 
        workflow: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Plan:
        """Create a dynamic plan from a workflow.
        
        A dynamic plan adapts during execution based on results.
        
        Args:
            workflow: Workflow graph
            objective: Execution objective
            upper_node: Node from the workflow layer to create plan for
            
        Returns:
            Dynamic plan
        """
        # For now, just create a direct plan
        # In the future, this would create a more adaptive plan
        return self._create_direct_graph(workflow, objective, upper_node)
    
    def _create_incremental_plan(
        self, 
        workflow: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Plan:
        """Create an incremental plan from a workflow.
        
        An incremental plan only plans a few steps ahead.
        
        Args:
            workflow: Workflow graph
            objective: Execution objective
            upper_node: Node from the workflow layer to create plan for
            
        Returns:
            Incremental plan
        """
        # For now, just create a direct plan
        # In the future, this would create a plan that evolves incrementally
        return self._create_direct_graph(workflow, objective, upper_node)
    
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build the planning context for a node.
        
        This method extends the base context with planning-specific information:
        1. Requirements and constraints
        2. Dependencies and resources
        
        Args:
            node: Node to build context for
            prev_signals: Signals from previous execution
            
        Returns:
            Planning context dictionary
        """
        # Get base context from parent class
        context = super()._build_layer_context(node, prev_signals)
        
        # Add planning-specific information
        context.update({
            "requirements": node.metadata.get("requirements", []),
            "constraints": node.metadata.get("constraints", []),
            "dependencies": node.metadata.get("dependencies", []),
            "resources": node.metadata.get("resources", [])
        })
        
        return context
