"""Optimal workflow executor implementation.

This module provides an optimized workflow executor that implements
a three-layer execution pattern with planning ahead and node optimization.
"""

from typing import List, cast

from ..execution_types import ExecutionNode, ExecutionSignal
from ..execution_graph import ExecutionGraph
from ..execution_context import ExecutionContext
from .workflow_executor import WorkflowExecutor
from .workflow_strategy import WorkflowStrategy
from ..planning import PlanStrategy
from ..reasoning import ReasoningStrategy


class OptimalWorkflowExecutor(WorkflowExecutor):
    """Executes workflows with optimized three-layer execution.
    
    This executor extends WorkflowExecutor to implement an optimized execution pattern that:
    1. Executes workflow nodes with planning ahead
    2. Optimizes planning layer nodes based on complexity
    3. Compresses reasoning layer steps when possible
    
    It inherits most functionality from WorkflowExecutor and only overrides
    the methods that need optimization.
    """

    def __init__(self,
                 workflow_strategy: WorkflowStrategy = WorkflowStrategy.DEFAULT,
                 planning_strategy: PlanStrategy = PlanStrategy.DEFAULT,
                 reasoning_strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT):
        super().__init__(workflow_strategy, planning_strategy, reasoning_strategy)
    
    async def _execute_lower_layer(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> List[ExecutionSignal]:
        """Execute the plan layer for a workflow node with optimizations.
        
        This method extends the base implementation to add optimization:
        1. Optimize planning layer nodes based on complexity
        2. Compress reasoning layer steps when possible
        
        Args:
            node: Node to execute lower layer for
            context: Execution context
            
        Returns:
            List of execution signals
        """
        # Create a new plan graph for this workflow node
        if not self.graph:
            raise RuntimeError("No graph set in workflow executor")
            
        assert self.lower_executor is not None, "Lower executor is not set"

        plan_graph = self.lower_executor.graph

        if plan_graph is None:
            # Generate a plan for this workflow node
            plan_graph = self.lower_executor.create_graph_from_upper_node(
                upper_node=node,
                upper_graph=self.graph,
                objective=self.graph.objective if self.graph else None,
                context=context
            )
        
        if plan_graph is None:
            self.logger.warning(f"No plan created for workflow node {node.node_id}")
            return []
        
        # Optimize planning layer nodes
        optimized_plan_graph = await self._optimize_planning_layer(
            plan_graph,
            context,
            []  # Since we removed _execute_workflow_layer, we don't have workflow signals
        )
            
        # Set the optimized plan in the lower executor
        self.lower_executor.graph = optimized_plan_graph
        
        # Set the plan in the context
        from ..planning import Plan
        context.current_plan = cast(Plan, optimized_plan_graph)
        
        # Execute the optimized plan
        return await self.lower_executor.execute_graph(optimized_plan_graph, context)
    
    async def _optimize_planning_layer(
        self,
        plan_graph: ExecutionGraph,
        context: ExecutionContext,
        workflow_signals: List[ExecutionSignal]
    ) -> ExecutionGraph:
        """Optimize the planning layer nodes.
        
        This method optimizes the planning layer by:
        1. Assessing node complexity
        2. Compressing nodes when possible
        3. Optimizing reasoning layer execution
        
        Args:
            plan_graph: Plan graph to optimize
            context: Execution context
            workflow_signals: Signals from workflow layer
            
        Returns:
            Optimized plan graph
        """
        # Create a new optimized plan graph
        optimized_graph = ExecutionGraph(
            objective=plan_graph.objective,
            layer="plan",
            name=f"{plan_graph.name}_optimized"
        )
        
        # Process each node in the plan
        for node in plan_graph.nodes.values():
            # Assess node complexity
            complexity = await self._assess_node_complexity(node, context, workflow_signals)
            
            if complexity > 0.7:  # High complexity threshold
                # Keep node as is for individual reasoning
                optimized_graph.add_node(node)
            else:
                # Compress node for optimized reasoning
                compressed_node = await self._compress_planning_node(node, context)
                optimized_graph.add_node(compressed_node)
        
        # Copy edges from original graph
        for edge in plan_graph.edges:
            optimized_graph.add_edge_between(edge.source, edge.target)
        
        return optimized_graph
    
    async def _assess_node_complexity(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        workflow_signals: List[ExecutionSignal]
    ) -> float:
        """Assess the complexity of a planning node.
        
        Args:
            node: Node to assess
            context: Execution context
            workflow_signals: Signals from workflow layer
            
        Returns:
            Complexity score between 0 and 1
        """
        # Build complexity assessment prompt
        prompt = f"""
Assess the complexity of the following planning node:
Node ID: {node.node_id}
Description: {node.description}
Metadata: {node.metadata}

Consider:
1. Number of required reasoning steps
2. Dependencies on other nodes
3. Amount of context needed
4. Potential for optimization

Return a complexity score between 0 and 1.
"""
        
        # Use LLM to assess complexity
        if context and context.reasoning_llm:
            response = await context.reasoning_llm.query({
                "prompt": prompt,
                "system_prompt": "You are assessing the complexity of a planning node.",
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 100
                }
            })
            
            try:
                # Extract score from response
                score = float(response.get("content", "0.5").strip())
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            except ValueError:
                return 0.5  # Default to medium complexity
        else:
            return 0.5  # Default to medium complexity
    
    async def _compress_planning_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> ExecutionNode:
        """Compress a planning node for optimized execution.
        
        Args:
            node: Node to compress
            context: Execution context
            
        Returns:
            Compressed node
        """
        # Create compressed node
        compressed_node = ExecutionNode(
            node_id=f"{node.node_id}_compressed",
            node_type=node.node_type,
            description=f"Compressed: {node.description}",
            metadata=node.metadata.copy()
        )
        
        # Add compression metadata
        compressed_node.metadata["compressed"] = True
        compressed_node.metadata["original_node_id"] = node.node_id
        
        # Build compression prompt
        prompt = f"""
Compress the following planning node for optimized execution:
Node ID: {node.node_id}
Description: {node.description}
Metadata: {node.metadata}

Consider:
1. Combine related reasoning steps
2. Remove redundant context
3. Optimize for efficiency
4. Maintain essential functionality

Return a compressed version of the node.
"""
        
        # Use LLM to compress node
        if context and context.reasoning_llm:
            response = await context.reasoning_llm.query({
                "prompt": prompt,
                "system_prompt": "You are compressing a planning node for optimized execution.",
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            })
            
            # Update compressed node with LLM suggestions
            if response and "content" in response:
                compressed_node.metadata["compression_notes"] = response["content"]
        
        return compressed_node 