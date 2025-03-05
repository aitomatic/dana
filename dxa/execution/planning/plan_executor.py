"""Plan executor implementation."""

import logging
from typing import List, Optional, TYPE_CHECKING

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal, Objective, ExecutionNodeStatus, ExecutionEdge
from ...common.graph import NodeType
from .plan import Plan
from .plan_strategy import PlanStrategy

if TYPE_CHECKING:
    from ..reasoning.reasoning_executor import ReasoningExecutor


class PlanExecutor(Executor[PlanStrategy]):
    """Executes plans by delegating to a reasoning executor.
    
    The PlanExecutor is responsible for executing plan graphs,
    which represent mid-level execution flows. It delegates the actual
    reasoning tasks to a ReasoningExecutor.
    """
    
    strategy_class = PlanStrategy
    default_strategy = PlanStrategy.DEFAULT
    
    def __init__(
        self, 
        reasoning_executor: 'ReasoningExecutor', 
        strategy: PlanStrategy = PlanStrategy.DEFAULT
    ):
        """Initialize plan executor.
        
        Args:
            reasoning_executor: Reasoning executor to use for executing reasoning tasks
            strategy: Plan execution strategy
        """
        super().__init__(depth=1)
        self.reasoning_executor = reasoning_executor
        self.strategy = strategy
        self.layer = "plan"
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a single node in the plan.
        
        This method handles the execution of a plan node by:
        1. Updating the node status
        2. Delegating to the reasoning executor based on the strategy
        3. Processing the results
        
        Args:
            node: Node to execute
            context: Execution context
            prev_signals: Signals from previous nodes
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals resulting from the node execution
        """
        self.logger.info(f"Executing plan node: {node.node_id}")
        
        try:
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Update node status to in progress
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Prepare node with strategy information
            node_metadata = node.metadata.copy() if node.metadata else {}
            node_metadata["plan_strategy"] = self.strategy.name
            
            # Create a copy of the node with updated metadata
            execution_node = ExecutionNode(
                node_id=node.node_id,
                node_type=node.node_type,
                description=node.description,
                metadata=node_metadata
            )
            
            # Execute the node using the reasoning executor
            signals = await self.reasoning_executor.execute_node(
                node=execution_node,
                context=context,
                prev_signals=prev_signals,
                upper_signals=upper_signals
            )
            
            # Update node status to completed
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error executing node {node.node_id}: {str(e)}")
            
            # Update node status to error
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.FAILED)
            
            # Create error signal
            return [self._create_error_signal(node.node_id, str(e))]
    
    async def _execute_task(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute the task associated with a plan node.
        
        This method implements the abstract method from the Executor base class.
        For the PlanExecutor, this delegates to execute_node which contains
        the actual implementation.
        
        Args:
            node: Node to execute
            context: Execution context
            prev_signals: Signals from previous nodes
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals resulting from the task execution
        """
        return await self.execute_node(
            node=node,
            context=context,
            prev_signals=prev_signals,
            upper_signals=upper_signals,
            lower_signals=lower_signals
        )
    
    def _create_graph(
        self, 
        upper_graph: ExecutionGraph, 
        objective: Optional[Objective] = None, 
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create a plan execution graph.
        
        For plan execution, the graph is created based on the planning strategy.
        
        Args:
            upper_graph: Graph from the upper execution layer (workflow)
            objective: Execution objective
            context: Execution context
            
        Returns:
            Plan execution graph
        """
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
        
        # Get workflow from context if available
        workflow = None
        # Check if context has a workflow attribute
        if context:
            workflow = context.current_workflow
            
        if not workflow:
            workflow = upper_graph
            
        if not workflow:
            # Create a minimal plan if no workflow is available
            return Plan(
                objective=objective or Objective("Execute plan"),
                name="default_plan"
            )
        
        # Create a plan based on the strategy
        if self.strategy == PlanStrategy.DEFAULT:
            # Direct execution - create a minimal plan that follows the workflow structure
            return self._create_direct_plan(workflow, objective)
        elif self.strategy == PlanStrategy.DYNAMIC:
            return self._create_dynamic_plan(workflow, objective)
        elif self.strategy == PlanStrategy.INCREMENTAL:
            return self._create_incremental_plan(workflow, objective)
        else:
            # Default to direct plan
            return self._create_direct_plan(workflow, objective)
    
    def _create_direct_plan(
        self, 
        workflow: ExecutionGraph, 
        objective: Optional[Objective] = None
    ) -> Plan:
        """Create a direct plan from a workflow.
        
        A direct plan follows the workflow structure directly.
        
        Args:
            workflow: Workflow graph
            objective: Execution objective
            
        Returns:
            Direct plan
        """
        # Create a plan that directly follows the workflow
        plan = Plan(
            objective=objective or workflow.objective,
            name=f"direct_plan_for_{workflow.name}"
        )
        
        # Copy nodes and edges from workflow
        for node in workflow.nodes.values():
            plan_node = ExecutionNode(
                node_id=node.node_id,
                node_type=node.node_type,
                description=node.description,
                metadata=node.metadata.copy() if node.metadata else {}
            )
            plan.add_node(plan_node)
            
        for edge in workflow.edges:
            plan_edge = ExecutionEdge(
                source=edge.source,
                target=edge.target,
                metadata=edge.metadata.copy() if edge.metadata else {}
            )
            plan.add_edge(plan_edge)
            
        return plan
    
    def _create_dynamic_plan(
        self, 
        workflow: ExecutionGraph, 
        objective: Optional[Objective] = None
    ) -> Plan:
        """Create a dynamic plan from a workflow.
        
        A dynamic plan adapts during execution based on results.
        
        Args:
            workflow: Workflow graph
            objective: Execution objective
            
        Returns:
            Dynamic plan
        """
        # For now, just create a direct plan
        # In the future, this would create a more adaptive plan
        return self._create_direct_plan(workflow, objective)
    
    def _create_incremental_plan(
        self, 
        workflow: ExecutionGraph, 
        objective: Optional[Objective] = None
    ) -> Plan:
        """Create an incremental plan from a workflow.
        
        An incremental plan only plans a few steps ahead.
        
        Args:
            workflow: Workflow graph
            objective: Execution objective
            
        Returns:
            Incremental plan
        """
        # For now, just create a direct plan
        # In the future, this would create a plan that evolves incrementally
        return self._create_direct_plan(workflow, objective)
    
    async def _custom_graph_traversal(
        self, 
        graph: ExecutionGraph, 
        context: ExecutionContext,
        upper_signals: Optional[List[ExecutionSignal]] = None
    ) -> Optional[List[ExecutionSignal]]:
        """Implement custom traversal strategies for plans.
        
        This method creates a reasoning graph based on the plan graph
        and sets it in the context before traversing the graph.
        
        Args:
            graph: Execution graph to traverse
            context: Execution context
            upper_signals: Signals from upper execution layer
            
        Returns:
            List of signals if custom traversal was performed, None otherwise
        """
        # Create a reasoning graph based on the plan graph
        reasoning_graph = self.reasoning_executor._create_graph(
            upper_graph=graph,
            objective=graph.objective,
            context=context
        )
        
        # Set the reasoning graph in the executor and context
        self.reasoning_executor.graph = reasoning_graph
        
        # Continue with default traversal
        return None 