"""Plan executor implementation."""

from typing import List, Optional, Dict, Any

from ...common import DXA_LOGGER
from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal, Objective
from .plan import Plan
from .plan_strategy import PlanStrategy


class PlanExecutor(Executor[PlanStrategy]):
    """Executes plans by delegating to a reasoning executor.
    
    The PlanExecutor is responsible for executing plan graphs,
    which represent mid-level execution flows. It delegates the actual
    reasoning tasks to a ReasoningExecutor.
    """
    
    @property
    def layer(self) -> str:
        """Get the execution layer name."""
        return "plan"
    
    @property
    def strategy_class(self) -> type[PlanStrategy]:
        """Get the strategy class for this executor."""
        return PlanStrategy
    
    @property
    def default_strategy(self) -> PlanStrategy:
        """Get the default strategy for this executor."""
        return PlanStrategy.DEFAULT
    
    def __init__(
        self, 
        strategy: PlanStrategy = PlanStrategy.DEFAULT
    ):
        """Initialize plan executor.
        
        Args:
            reasoning_executor: Reasoning executor to use for executing reasoning tasks
            strategy: Plan execution strategy
        """
        super().__init__(depth=1)
        self.strategy = strategy
        self.logger = DXA_LOGGER.getLogger(f"dxa.execution.{self.layer}")
    
    def _get_graph_class(self):
        """Get the appropriate graph class for this executor.
        
        Returns:
            Plan graph class
        """
        # Import here to avoid circular import
        return Plan
    
    def create_graph_from_upper_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> Optional[ExecutionGraph]:
        """Create a plan execution graph from a node in the workflow.
        
        This method creates a plan graph based on a workflow node.
        
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
            return Plan(
                objective=objective or Objective(f"Execute plan for {upper_node.node_id}"),
                name=f"plan_for_{upper_node.node_id}"
            )
        
        # Create a plan based on the strategy
        if self.strategy == PlanStrategy.DEFAULT:
            # Direct execution - create a minimal plan that follows the workflow structure
            return self._create_direct_plan(workflow, objective, upper_node)
        elif self.strategy == PlanStrategy.DYNAMIC:
            return self._create_dynamic_plan(workflow, objective, upper_node)
        elif self.strategy == PlanStrategy.INCREMENTAL:
            return self._create_incremental_plan(workflow, objective, upper_node)
        else:
            # Default to direct plan
            return self._create_direct_plan(workflow, objective, upper_node)
            
    def _create_direct_plan(
        self, 
        workflow: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Plan:
        """Create a direct plan from a workflow.
        
        A direct plan follows the workflow structure directly.
        
        Args:
            workflow: Workflow graph
            objective: Execution objective
            upper_node: Node from the workflow layer to create plan for
            
        Returns:
            Direct plan
        """
        # Create a plan that directly follows the workflow
        node_id = upper_node.node_id if upper_node else "workflow"
        plan = Plan(
            objective=objective or workflow.objective,
            name=f"direct_plan_for_{node_id}"
        )
        
        # Create nodes based on workflow structure
        for node in workflow.nodes.values():
            # Create a copy of the node's metadata
            metadata = node.metadata.copy() if node.metadata else {}
            
            # Ensure prompt is passed through
            if "prompt" in metadata:
                metadata["prompt"] = metadata["prompt"]
            
            plan_node = ExecutionNode(
                node_id=node.node_id,
                node_type=node.node_type,
                description=node.description,
                metadata=metadata
            )
            
            # If this is the upper node, add additional metadata
            if upper_node and node.node_id == upper_node.node_id:
                plan_node.metadata["is_upper_node"] = True
                plan_node.metadata["upper_node_id"] = upper_node.node_id
            
            plan.add_node(plan_node)
        
        # Create edges based on workflow structure
        for edge in workflow.edges:
            plan.add_edge_between(edge.source, edge.target)
        
        return plan
    
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
        return self._create_direct_plan(workflow, objective, upper_node)
    
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
        return self._create_direct_plan(workflow, objective, upper_node)
    
    def _process_previous_signals(self, signals: List[ExecutionSignal]) -> Dict[str, Any]:
        """Process previous signals to extract outputs.
        
        Args:
            signals: List of previous execution signals
            
        Returns:
            Dictionary mapping node IDs to their outputs
        """
        return {
            str(signal.content.get("node")): signal.content.get("output")
            for signal in signals
            if signal.type == "output"
        }
    
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build the planning context for a node.
        
        This method builds the context needed for plan layer execution,
        including:
        1. Node information
        2. Previous execution results
        3. Planning-specific metadata
        4. Requirements and constraints
        
        Args:
            node: Node to build context for
            prev_signals: Signals from previous execution
            
        Returns:
            Planning context dictionary
        """
        context = {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "description": node.description,
            "metadata": node.metadata or {}
        }
        
        # Add planning-specific information
        context.update({
            "requirements": node.metadata.get("requirements", []),
            "constraints": node.metadata.get("constraints", []),
            "dependencies": node.metadata.get("dependencies", []),
            "resources": node.metadata.get("resources", [])
        })
        
        # Add previous outputs if available
        if prev_signals:
            context["previous_outputs"] = {
                signal.content.get("node"): signal.content.get("output")
                for signal in prev_signals
                if signal.type == "output"
            }
        
        return context
