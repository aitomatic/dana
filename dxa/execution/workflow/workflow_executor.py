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

if TYPE_CHECKING:
    from ..planning.plan_executor import PlanExecutor
    from ..planning.plan import Plan
    from ..reasoning.reasoning import Reasoning


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
        """Initialize workflow executor.
        
        Args:
            plan_executor: Plan executor to use for executing plans
            strategy: Workflow execution strategy
        """
        super().__init__(depth=0)
        self.plan_executor = plan_executor
        self.strategy = strategy
        self.layer = "workflow"
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
    
    async def execute_workflow(self, workflow: ExecutionGraph, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a workflow graph.
        
        Args:
            workflow: The workflow graph to execute
            context: The execution context
            
        Returns:
            List of execution signals
        """
        self.logger.info(f"Executing workflow: {workflow.name if workflow.name else 'unnamed'}")
        
        # Set the current graph to the workflow
        self.graph = workflow
        context.current_workflow = cast(Workflow, workflow)
        
        # Import here to avoid circular imports
        from ..planning.plan import Plan
        from ..reasoning.reasoning import Reasoning
        
        # Create a plan graph and set it in the context
        plan = self.plan_executor._create_graph(workflow, workflow.objective, context)
        context.current_plan = cast(Plan, plan)
        
        # Also set the plan in the plan executor
        self.plan_executor.graph = plan
        
        # Create a reasoning graph and set it in the context
        reasoning = self.plan_executor.reasoning_executor._create_graph(plan, workflow.objective, context)
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
        """Execute a single node in the workflow.
        
        This method handles the execution of a workflow node by:
        1. Updating the node status
        2. Delegating to the plan executor based on the strategy
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
        self.logger.info(f"Executing workflow node: {node.node_id}")
        
        try:
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Update node status to in progress
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Handle WORKFLOW_IS_PLAN strategy
            if self.strategy == WorkflowStrategy.WORKFLOW_IS_PLAN:
                # Create a pass-through plan that directly delegates to reasoning
                pass_through_plan = self._create_pass_through_plan(node)
                
                # Set the plan in the context
                if context:
                    context.current_plan = pass_through_plan
                
                # Execute the plan using the plan executor
                signals = await self.plan_executor.execute_graph(
                    upper_graph=pass_through_plan,
                    context=context,
                    upper_signals=upper_signals
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
            
        except Exception as e:
            self.logger.error(f"Error executing node {node.node_id}: {str(e)}")
            
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
    
    def _create_graph(
        self, 
        upper_graph: ExecutionGraph, 
        objective: Optional[Objective] = None, 
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create a workflow execution graph.
        
        For workflow execution, the graph is typically provided directly
        rather than being created from an upper graph.
        
        Args:
            upper_graph: Graph from the upper execution layer
            objective: Execution objective
            context: Execution context
            
        Returns:
            Workflow execution graph
        """
        # For workflow, we typically use the provided graph directly
        # This method is mainly here to satisfy the abstract method requirement
        
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
        
        # Otherwise, use the upper graph if it's provided
        if upper_graph is not None:
            workflow = upper_graph
        else:
            # If no graph is available, create a minimal one
            workflow = Workflow(
                objective=objective or Objective("Execute workflow"),
                name="default_workflow"
            )
        
        # Create a plan graph and set it in the context
        if context is not None:
            plan = self.plan_executor._create_graph(
                upper_graph=workflow,
                objective=workflow.objective,
                context=context
            )
            self.plan_executor.graph = plan
            
            # Set the plan in the context
            from ..planning import Plan
            context.current_plan = cast(Plan, plan)
            
            # Create a reasoning graph and set it in the context
            reasoning = self.plan_executor.reasoning_executor._create_graph(
                upper_graph=plan,
                objective=workflow.objective,
                context=context
            )
            self.plan_executor.reasoning_executor.graph = reasoning
            
            # Set the reasoning in the context
            from ..reasoning import Reasoning
            context.current_reasoning = cast(Reasoning, reasoning)
        
        return workflow 