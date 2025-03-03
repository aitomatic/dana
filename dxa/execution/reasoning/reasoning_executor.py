"""Reasoning executor implementation."""

import logging
from typing import List, Optional

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionNode, ExecutionSignal, Objective, ExecutionNodeStatus
from ...common.graph import NodeType
from .reasoning_strategy import ReasoningStrategy


class ReasoningExecutor(Executor[ReasoningStrategy]):
    """Executes reasoning tasks using LLM-based reasoning.
    
    The ReasoningExecutor is responsible for executing reasoning tasks,
    which represent low-level execution steps. It uses LLM-based reasoning
    to perform the actual work.
    """
    
    strategy_class = ReasoningStrategy
    default_strategy = ReasoningStrategy.DEFAULT
    
    def __init__(
        self, 
        strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT
    ):
        """Initialize reasoning executor.
        
        Args:
            strategy: Reasoning strategy
        """
        super().__init__(depth=2)
        self.strategy = strategy
        self.layer = "reasoning"
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a single node in the reasoning layer.
        
        This method handles the execution of a reasoning node by:
        1. Updating the node status
        2. Executing the reasoning task based on the strategy
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
        self.logger.info(f"Executing reasoning node: {node.node_id}")
        
        try:
            # Check if this is a pass-through node from WORKFLOW_IS_PLAN
            is_pass_through = False
            if node.metadata and node.metadata.get("is_pass_through", False):
                is_pass_through = True
                self.logger.info(f"Executing pass-through node {node.node_id} from WORKFLOW_IS_PLAN")
            
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Update node status to in progress (only if not a pass-through node)
            if self.graph and not is_pass_through:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Get the instruction from the node
            instruction = node.description
            
            # Get previous steps if available
            prev_steps = ""
            if prev_signals:
                prev_steps = "\n".join([
                    signal.content.get("result", "") 
                    for signal in prev_signals 
                    if "result" in signal.content
                ])
            
            # Get objective from node metadata, context, or default
            objective_text = "Complete the task"
            
            # First check node metadata for workflow objective (highest priority)
            if node.metadata and "workflow_objective" in node.metadata:
                obj = node.metadata["workflow_objective"]
                if hasattr(obj, "current"):
                    objective_text = obj.current
                else:
                    objective_text = str(obj)
            # Then check context for plan objective
            elif context and context.current_plan and context.current_plan.objective:
                objective_text = context.current_plan.objective.current
            
            # Execute the reasoning task
            result = await self._execute_reasoning(
                node=node,
                context=context,
                instruction=instruction,
                prev_steps=prev_steps,
                objective=objective_text
            )
            
            # Update node status to completed (only if not a pass-through node)
            if self.graph and not is_pass_through:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
            
            # Create result signal
            return [self.create_result_signal(node.node_id, result)]
            
        except Exception as e:
            self.logger.error(f"Error executing node {node.node_id}: {str(e)}")
            
            # Update node status to error (only if not a pass-through node)
            if self.graph and not is_pass_through:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.FAILED)
            
            # Create error signal
            return [self.create_error_signal(node.node_id, str(e))]
    
    async def _execute_task(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute the task associated with a reasoning node.
        
        This method implements the abstract method from the Executor base class.
        For the ReasoningExecutor, this delegates to execute_node which contains
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
    
    async def _execute_reasoning(
        self, 
        node: ExecutionNode, 
        context: ExecutionContext,
        instruction: str, 
        prev_steps: str, 
        objective: str,
        max_tokens: int = 1000
    ) -> str:
        """Execute a reasoning task.
        
        This method simulates the execution of a reasoning task by:
        1. Creating a prompt template
        2. Executing the reasoning with the appropriate strategy
        3. Returning the result
        
        Args:
            node: Node to execute
            context: Execution context
            instruction: Instruction for the reasoning task
            prev_steps: Previous steps in the reasoning process
            objective: Objective of the reasoning task
            max_tokens: Maximum tokens for the response
            
        Returns:
            Result of the reasoning task
        """
        self.logger.info(f"Executing reasoning task: {instruction}")
        
        # For now, just simulate the LLM call
        # In a real implementation, this would use the reasoning_llm from context
        
        # Create a simple result based on the node ID and strategy
        result = f"Reasoning result for node {node.node_id} using strategy {self.strategy.name}"
        
        return result
    
    def _create_graph(
        self, 
        upper_graph: ExecutionGraph, 
        objective: Optional[Objective] = None, 
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create a reasoning execution graph.
        
        For reasoning execution, the graph is typically created from the plan graph.
        
        Args:
            upper_graph: Graph from the upper execution layer (plan)
            objective: Execution objective
            context: Execution context
            
        Returns:
            Reasoning execution graph
        """
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
        
        # Create a new reasoning graph
        graph = ExecutionGraph(
            objective=objective or (upper_graph.objective if upper_graph else Objective("Execute reasoning")),
            name=f"reasoning_for_{upper_graph.name if upper_graph else 'unnamed'}"
        )
        
        # Copy nodes and edges from upper graph if available
        if upper_graph:
            for node_id, node in upper_graph.nodes.items():
                graph.add_node(
                    ExecutionNode(
                        node_id=node.node_id,
                        node_type=node.node_type,
                        description=node.description,
                        metadata=node.metadata.copy() if node.metadata else {}
                    )
                )
                
            for edge in upper_graph.edges:
                graph.add_edge_between(edge.source, edge.target)
        
        return graph 