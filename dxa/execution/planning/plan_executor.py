"""Plan executor implementation."""

import logging
from typing import List, Optional, TYPE_CHECKING, cast, Dict, Any

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal, Objective, ExecutionNodeStatus, ExecutionEdge
from ...common.graph import NodeType
from .plan import Plan
from .plan_strategy import PlanStrategy

if TYPE_CHECKING:
    from ..reasoning.reasoning_executor import ReasoningExecutor
    from ..reasoning.reasoning import Reasoning


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
        reasoning_executor: 'ReasoningExecutor', 
        strategy: PlanStrategy = PlanStrategy.DEFAULT
    ):
        """Initialize plan executor.
        
        Args:
            reasoning_executor: Reasoning executor to use for executing reasoning tasks
            strategy: Plan execution strategy
        """
        super().__init__(depth=1)
        self.lower_executor = reasoning_executor
        self.strategy = strategy
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
    
    def _get_graph_class(self):
        """Get the appropriate graph class for this executor.
        
        Returns:
            Plan graph class
        """
        # Import here to avoid circular import
        from .plan import Plan
        return Plan
    
    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a plan node.
        
        Args:
            node: Node to execute
            context: Execution context
            prev_signals: Signals from previous node execution
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals
        """
        try:
            # Log node execution
            self.logger.info("Executing plan node: %s", node.node_id)
            
            # Update node status
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Prepare node metadata
            node_metadata = node.metadata.copy() if node.metadata else {}
            
            # Add planning context
            planning_context = {
                "current_node": node.node_id,
                "plan_state": node.status.name if hasattr(node, 'status') else 'UNKNOWN',
                "requirements": node_metadata.get("requirements", []),
                "constraints": node_metadata.get("constraints", [])
            }
            
            # Add planning context to metadata
            node_metadata["planning_context"] = planning_context
            
            # Create execution node with updated metadata
            execution_node = ExecutionNode(
                node_id=node.node_id,
                node_type=node.node_type,
                description=node.description,
                metadata=node_metadata
            )
            
            # Create a new reasoning graph for this plan node
            if not self.graph:
                raise RuntimeError("No graph set in plan executor")
                
            reasoning = self.lower_executor.create_graph_from_node(
                upper_node=execution_node,
                upper_graph=self.graph,
                objective=self.graph.objective if self.graph else None,
                context=context
            )
            
            # Set the reasoning in context and execute it
            context.current_reasoning = cast(Reasoning, reasoning)
            self.lower_executor.graph = reasoning
            signals = await self.lower_executor.execute_graph(reasoning, context)
            
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
    
    def create_graph_from_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
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
        # Get the current node from the cursor position
        cursor_pos = getattr(graph, 'cursor_position', None)
        if cursor_pos and cursor_pos in graph.nodes:
            current_node = graph.nodes[cursor_pos]
        else:
            # Default to start node
            current_node = graph.get_start_node()
        
        if current_node:
            # Create a reasoning graph for the current node
            reasoning_graph = self.lower_executor.create_graph_from_node(
                upper_node=current_node,
                upper_graph=graph,
                objective=graph.objective if graph else None,
                context=context
            )
            
            # Set the reasoning graph in the reasoning executor
            self.lower_executor.graph = reasoning_graph
            
            # Execute the current node using the reasoning executor
            return await self.lower_executor.execute_node(
                node=current_node,
                context=context,
                upper_signals=upper_signals
            )
        
        return None 
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
        """Build plan context for node execution.
        
        Args:
            node: Node to execute
            prev_signals: Signals from previous node execution
            
        Returns:
            Plan context dictionary
        """
        # Get base context from parent
        context = super()._build_layer_context(node, prev_signals)
        
        # Add plan-specific context
        if prev_signals:
            context["previous_outputs"] = self._process_previous_signals(prev_signals)
        
        return context
    
    async def _execute_next_layer(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute the reasoning layer for the given node.
        
        Args:
            node: Node to execute
            context: Execution context
            
        Returns:
            List of execution signals
        """
        if not self.graph:
            raise RuntimeError("No graph set for plan execution")
            
        if not self.lower_executor:
            raise RuntimeError("No reasoning executor set")
            
        # Assert that lower_executor is not None for type checker
        lower_executor = cast('ReasoningExecutor', self.lower_executor)
            
        # Create reasoning graph from plan node
        reasoning_graph = lower_executor.create_graph_from_node(
            upper_node=node,
            upper_graph=self.graph,
            objective=self.graph.objective if self.graph else None,
            context=context
        )
        
        # Cast to Reasoning type
        reasoning = cast('Reasoning', reasoning_graph)
        
        # Set reasoning graph in context
        context.current_reasoning = reasoning
        
        # Execute reasoning graph
        return await lower_executor.execute_graph(reasoning, context) 
