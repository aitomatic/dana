"""Workflow executor implementation."""

import logging
from typing import List, Optional, TYPE_CHECKING, cast

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal, Objective, ExecutionNodeStatus
from ...common.graph import NodeType
from .workflow_strategy import WorkflowStrategy
from .workflow import Workflow
from .workflow_factory import WorkflowFactory

if TYPE_CHECKING:
    from ..planning.plan_executor import PlanExecutor
    from ..planning.plan import Plan


class WorkflowExecutor(Executor[WorkflowStrategy]):
    """Executes workflows by delegating to a plan executor.
    
    The WorkflowExecutor is responsible for executing workflow graphs,
    which represent high-level execution flows. It delegates the actual
    execution of tasks to a PlanExecutor.
    """
    
    strategy_class = WorkflowStrategy
    default_strategy = WorkflowStrategy.DEFAULT
    
    def __init__(
        self, 
        plan_executor: 'PlanExecutor', 
        strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT
    ):
        """Initialize the workflow executor.
        
        Args:
            plan_executor: Plan executor to use for executing plans
            strategy: Workflow execution strategy
        """
        super().__init__(depth=0)
        self.plan_executor = plan_executor
        self.strategy = strategy
        self.layer = "workflow"
        self.logger = logging.getLogger("dxa.execution.%s" % self.layer)
    
    async def execute_workflow(self, workflow: ExecutionGraph, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a workflow graph.
        
        Args:
            workflow: The workflow graph to execute
            context: The execution context
            
        Returns:
            List of execution signals
        """
        self.logger.info("Executing workflow: %s", workflow.name if workflow.name else 'unnamed')
        
        # Set the current graph to the workflow
        self.graph = workflow
        context.current_workflow = cast(Workflow, workflow)
        
        # Import here to avoid circular imports
        from ..planning.plan import Plan
        from ..reasoning.reasoning import Reasoning
        
        # Get the start node of the workflow
        start_node = workflow.get_start_node()
        if not start_node:
            self.logger.error("Workflow has no START node")
            return []
        
        # Create a plan graph from the workflow's start node and set it in the context
        plan = self.plan_executor.create_graph_from_node(
            upper_node=start_node, 
            upper_graph=workflow, 
            objective=workflow.objective, 
            context=context
        )
        context.current_plan = cast(Plan, plan)
        
        # Also set the plan in the plan executor
        self.plan_executor.graph = plan
        
        # Get the start node of the plan
        plan_start_node = plan.get_start_node()
        if not plan_start_node:
            self.logger.error("Plan has no START node")
            return []
        
        # Create a reasoning graph from the plan's start node and set it in the context
        reasoning = self.plan_executor.reasoning_executor.create_graph_from_node(
            upper_node=plan_start_node,
            upper_graph=plan, 
            objective=workflow.objective,
            context=context
        )
        context.current_reasoning = cast(Reasoning, reasoning)
        
        # Also set the reasoning in the reasoning executor
        self.plan_executor.reasoning_executor.graph = reasoning
        
        # Execute the graph
        signals = await self.execute_graph(workflow, context)
        
        # Update cursor to the END node after execution
        terminal_nodes = workflow.get_terminal_nodes()
        if terminal_nodes and len(terminal_nodes) > 0:
            workflow.update_cursor(terminal_nodes[0].node_id)
        
        return signals
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a workflow node.
        
        Args:
            node: The node to execute
            context: The execution context
            prev_signals: Signals from previous node execution
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals
        """
        try:
            # Log node execution
            self.logger.info("Executing workflow node: %s", node.node_id)
            
            # Update node status
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Handle WORKFLOW_IS_PLAN strategy
            if self.strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
                # Create a pass-through plan that directly delegates to reasoning
                pass_through_plan = self._create_pass_through_plan(node)
                
                # Set the plan in the context
                if context:
                    context.current_plan = pass_through_plan
                
                # Execute the plan using the plan executor with the workflow node
                signals = await self.plan_executor.execute_graph(
                    upper_graph=pass_through_plan,
                    context=context,
                    upper_signals=upper_signals,
                    upper_node=node  # Pass the workflow node to create reasoning graph
                )
            else:
                # For DEFAULT strategy, just delegate to the plan executor
                signals = await self.plan_executor.execute_node(
                    node=node,
                    context=context,
                    prev_signals=prev_signals,
                    upper_signals=upper_signals
                )
            
            # Update node status to completed
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
            
            return signals
            
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("Error executing node %s: %s", node.node_id, str(e))
            
            # Update node status to error
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.FAILED)
            
            # Create error signal
            return [self._create_error_signal(node.node_id, str(e))]
    
    def _create_pass_through_plan(self, node: ExecutionNode) -> 'Plan':
        """Create a pass-through plan for WORKFLOW_IS_PLAN strategy.
        
        This creates a minimal plan with a single task node that directly
        passes the workflow objective to the reasoning layer.
        
        Args:
            node: The workflow node to execute
            
        Returns:
            A pass-through plan
        """
        from ..planning.plan import Plan
        
        # Create a plan with the workflow objective
        objective = None
        if self.graph and self.graph.objective:
            objective = self.graph.objective
        
        plan = Plan(
            objective=objective,
            name=f"pass_through_plan_for_{node.node_id}"
        )
        
        # Add START node
        start_node = ExecutionNode(
            node_id="START",
            node_type=NodeType.START,
            description="Start pass-through plan"
        )
        plan.add_node(start_node)
        
        # Add task node with the original node's description and metadata
        task_node = ExecutionNode(
            node_id=node.node_id,
            node_type=NodeType.TASK,
            description=node.description,
            metadata={
                # Include original node metadata
                **(node.metadata or {}),
                # Add workflow objective for reasoning executor
                "workflow_objective": objective,
                # Mark as pass-through for reasoning executor
                "is_pass_through": True
            }
        )
        plan.add_node(task_node)
        
        # Add END node
        end_node = ExecutionNode(
            node_id="END",
            node_type=NodeType.END,
            description="End pass-through plan"
        )
        plan.add_node(end_node)
        
        # Connect nodes
        plan.add_edge_between("START", node.node_id)
        plan.add_edge_between(node.node_id, "END")
        
        return plan
    
    def _get_graph_class(self):
        """Get the appropriate graph class for this executor.
        
        Returns:
            Workflow graph class
        """
        from .workflow import Workflow
        return Workflow
    
    def create_graph_from_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create a workflow execution graph from a node in an upper layer.
        
        For workflow execution, the graph is typically provided directly
        rather than being created from an upper graph. 
        
        Workflows are the top-level execution layer, so this method
        is mostly provided to satisfy the interface.
        
        Args:
            upper_node: Node from upper layer (rarely used for workflows)
            upper_graph: Graph from upper layer (rarely used for workflows)
            objective: Execution objective
            context: Execution context
            
        Returns:
            Workflow execution graph
        """
        # For workflows, we typically use the provided graph directly
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph

        # Create a new workflow if we don't have one
        
        # Create a minimal workflow with START, TASK, and END nodes
        node_id = upper_node.node_id if upper_node else 'unknown'
        workflow_objective = objective or Objective(f"Execute workflow for {node_id}")
        
        # Use the factory to create a proper workflow with all required nodes
        return WorkflowFactory.create_minimal_workflow(workflow_objective)