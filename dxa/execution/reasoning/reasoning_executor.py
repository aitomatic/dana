"""Reasoning executor implementation."""

import logging
from typing import List, Optional

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import (
    ExecutionNode, 
    ExecutionSignal, 
    Objective, 
    ExecutionNodeStatus,
    ExecutionSignalType
)
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
        2. Executing the reasoning task
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
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Update node status to in progress
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Get the instruction from the node metadata
            instruction = node.metadata.get("instruction", "")
            if not instruction and node.metadata.get("description"):
                instruction = node.metadata.get("description", "")
            
            # If no instruction, use the node ID
            if not instruction:
                instruction = f"Execute task {node.node_id}"
            
            # Get the objective from the graph
            objective = None
            if self.graph and hasattr(self.graph, "objective"):
                objective = self.graph.objective
            
            # Execute the reasoning task
            result = await self._execute_reasoning_task(
                node=node,
                context=context,
                instruction=instruction,
                prev_steps=None,  # We don't have previous steps yet
                objective=objective,
                max_tokens=1000
            )
            
            # Update node status to completed
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
            
            # Create result signal
            signal = ExecutionSignal(
                type=ExecutionSignalType.DATA_RESULT,
                content={
                    "node": node.node_id,
                    "result": result
                }
            )
            
            return [signal]
            
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
    
    async def _execute_reasoning_task(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        instruction: str,
        prev_steps: Optional[List[str]] = None,
        objective: Optional[Objective] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Execute a reasoning task using LLM.
        
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
        
        # Use the reasoning_llm from context to generate a response
        if context and context.reasoning_llm:
            try:
                # Prepare the prompt
                prompt = instruction
                if objective:
                    # Access the objective text safely
                    objective_text = getattr(objective, "description", str(objective))
                    prompt = f"Objective: {objective_text}\n\nTask: {instruction}"
                
                # Add previous steps if available
                if prev_steps and len(prev_steps) > 0:
                    steps_text = "\n".join([f"- {step}" for step in prev_steps])
                    prompt = f"{prompt}\n\nPrevious steps:\n{steps_text}"
                
                # Query the LLM
                response = await context.reasoning_llm.query({
                    "prompt": prompt,
                    "system_prompt": (
                        "You are a helpful AI assistant. "
                        "Provide a clear, accurate, and detailed response."
                    ),
                    "parameters": {
                        "temperature": 0.7,
                        "max_tokens": max_tokens or 1000
                    }
                })
                
                # Extract and return the content
                if response and "content" in response:
                    return response["content"]
                else:
                    self.logger.error("LLM response did not contain content")
                    return "Error: LLM response did not contain content"
                    
            except Exception as e:
                self.logger.error(f"Error executing reasoning task: {str(e)}")
                return f"Error executing reasoning task: {str(e)}"
        else:
            # Fallback to placeholder if no LLM is available
            self.logger.warning("No reasoning LLM available in context, using placeholder")
            return f"Reasoning result for node {node.node_id} using strategy {self.strategy.name}"
    
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