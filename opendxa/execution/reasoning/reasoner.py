"""Reasoning executor implementation."""

import logging
from typing import List, Optional

from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.base.execution.execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionSignalType,
    Objective,
    ExecutionEdge,
)
from opendxa.base.execution.base_executor import BaseExecutor
from opendxa.base.resource import LLMResource
from opendxa.execution.reasoning.reasoning import Reasoning
from opendxa.execution.reasoning.reasoning_factory import ReasoningFactory
from opendxa.execution.reasoning.reasoning_strategy import ReasoningStrategy
from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.common.graph import NodeType
from opendxa.common.types import BaseRequest, BaseResponse


log = logging.getLogger(__name__)

class Reasoner(BaseExecutor[ReasoningStrategy, Reasoning, ReasoningFactory]):
    """Executor for reasoning layer tasks.
    This executor handles the reasoning layer of execution, which is
    the bottom-most layer responsible for making actual calls to the LLM
    using the strategy provided.
    """

    # Required class attributes
    _strategy_type = ReasoningStrategy
    _default_strategy = ReasoningStrategy.DEFAULT
    graph_class = Reasoning
    _factory_class = ReasoningFactory
    _depth = 2

    def __init__(self, 
                 strategy: Optional[ReasoningStrategy] = None, 
                 reasoning_llm: Optional[LLMResource] = None):
        """Initialize reasoner.
        
        Args:
            strategy: Reasoning strategy
            reasoning_llm: LLM resource for reasoning tasks
        """
        super().__init__(strategy=strategy)
        self._reasoning_llm = reasoning_llm
        if self._reasoning_llm is None:
            self.warning("Reasoner initialized without an LLM resource.")

    async def _execute_node_core(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a reasoning node using LLM.

        This is the bottom layer executor, so it handles the actual execution
        of reasoning tasks using LLMs.

        Args:
            node: The node to execute
            context: The execution context

        Returns:
            List of execution signals
        """
        # Get parent nodes
        plan_node = context.get_current_plan_node()

        # Print concise execution hierarchy
        self.info("\nExecution Context:")
        self.info("=================")
        
        if plan_node:
            plan_obj = context.current_plan.objective if hasattr(context, 'current_plan') and context.current_plan else None
            self.info(f"Plan: {plan_node.node_type} - {plan_node.description}")
            self.info(f"  Objective: {plan_obj if plan_obj else 'None'}")

            self.info(f"  Reasoning: {node.node_type} - {node.description}")
            self.info(f"    Objective: {node.objective if node.objective else 'None'}")

            # Make LLM call using the stored LLM resource
            if self._reasoning_llm and node.objective:
                # Build prompt components
                user_messages = self._build_user_messages(context)
                system_messages = self._build_system_messages()
                
                # Construct the request for the LLM query
                request_args = {
                    "user_messages": user_messages,
                    "system_messages": system_messages,
                    # Add other parameters like max_tokens, temperature if needed
                    # "max_tokens": 1000,
                    # "temperature": 0.7,
                    # Pass available tools/resources if the strategy requires them
                    # "available_resources": context.available_resources or {}
                }
                request = BaseRequest(arguments=request_args)
                
                # Call the LLM query method
                response: BaseResponse = await self._reasoning_llm.query(request)
                self.info(f"LLM Response: {response.content}")
                
                # Create a signal with the result
                result_signal = ExecutionSignal(
                    type=ExecutionSignalType.DATA_RESULT if response.success else ExecutionSignalType.CONTROL_ERROR,
                    content=response.content  # Use the content from BaseResponse
                )
                return [result_signal]
            
            # No LLM or objective, return empty list or default signal?
            self.warning("No reasoning LLM or objective found, cannot execute reasoning node.")
            return []

        # Fallback if plan_node is not found
        self.warning("Plan node not found in context, cannot execute reasoning node.")
        return []

    def _build_reasoning_directives(self, strategy: ReasoningStrategy) -> List[str]:
        """Build the reasoning strategy section of the prompt.

        Args:
            strategy: The reasoning strategy to use

        Returns:
            List of strings for the reasoning strategy section
        """
        result = ["Here is your reasoning strategy:"]

        if strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            result.extend([
                "Reasoning: Following tree-of-thought strategy:",
                "  1. Identify multiple possible approaches to the problem",
                "  2. Explore each approach systematically",
                "  3. Evaluate the strengths and weaknesses of each path",
                "  4. Select and refine the most promising solution"
            ])
        elif strategy == ReasoningStrategy.REFLECTION:
            result.extend([
                "Reasoning: Following reflection strategy:",
                "  1. Analyze the problem and initial solution",
                "  2. Critically evaluate the solution's effectiveness",
                "  3. Identify potential improvements and refinements",
                "  4. Implement and validate the enhanced solution"
            ])
        elif strategy == ReasoningStrategy.OODA:
            result.extend([
                "Reasoning: Following OODA loop strategy.",
                "  1. Observe: Gather and analyze current context and requirements",
                "  2. Orient: Understand the situation and identify key factors",
                "  3. Decide: Formulate a clear approach and decision",
                "  4. Act: Execute the reasoning task with the chosen approach",
            ])
        else:  # Default to CHAIN_OF_THOUGHT
            result.extend([
                "Reasoning: Following chain-of-thought strategy:",
                "  1. Break down the problem into sequential steps",
                "  2. Analyze each step carefully and thoroughly",
                "  3. Connect the steps logically to form a coherent solution",
                "  4. Verify the solution's completeness and correctness"
            ])
        
        result.extend([
            "Repeat the above process exactly 3 times, or until you are confident that the task is complete and the objective is met."
            "At the end, you must always provide an assessement of whether the objective has been met or not."
        ])
        return result

    def _build_user_messages(self, context: ExecutionContext) -> List[str]:
        """Build the user messages for the reasoning node.

        Args:
            context: The execution context

        Returns:
            The user messages for the reasoning node
        """
        # Get current plan node and overall plan information
        plan_node = context.get_current_plan_node()
        plan_obj = context.current_plan.objective if context.current_plan else None
        plan_nodes = context.current_plan.nodes if context.current_plan else {}

        user_messages = [
            "PLAN OVERVIEW:",
            f"- Overall Plan Objective: {plan_obj if plan_obj else 'None'}",
            "",
            "EXECUTION GRAPH:",
        ]

        # Add plan nodes sequence
        for i, plan_node_iter in enumerate(plan_nodes.values(), 1):
            current_plan_node = context.get_current_plan_node()
            is_current_plan = (
                plan_node_iter.node_id == current_plan_node.node_id 
                if plan_node_iter and current_plan_node 
                else False
            )
            current_marker = " [CURRENT]" if is_current_plan else ""
            user_messages.extend([
                f"{i}. {plan_node_iter.node_type}: {plan_node_iter.description}{current_marker}",
                f"   - Objective: {plan_node_iter.objective if plan_node_iter.objective else 'None'}",
                f"   - Status: {plan_node_iter.status}",
            ])

        user_messages.extend([
            "",
            "CURRENT EXECUTION CONTEXT:",
            f"- Plan: {plan_node.description if plan_node else 'None'} ({plan_node.status if plan_node else 'None'})",
        ])

        return user_messages

    def _build_system_messages(self) -> List[str]:
        """Build the system messages for the reasoning node.

        Returns:
            The system messages for the reasoning node
        """
        system_messages = []
        system_messages.extend([
            "You are executing a reasoning task. Provide clear, logical analysis and reasoning.",
            "You are operating within a two-layer execution hierarchy: Plan -> Reasoning.",
            "The Plan layer is typically generated dynamically to accomplish the objective",
            "The Reasoning layer is typically a choice of several fundamental strategies, e.g., "
            "chain-of-thought, tree-of-thought, reflection, OODA loop, etc.",
            "",
            "You are currently in the Reasoning layer. Execute the reasoning task while keeping in mind:",
            " 1. The specific plan that this reasoning task is part of",
            " 2. The immediate reasoning task requirements",
            "",
        ])

        self.debug(f"Reasoning Strategy: {self.strategy}")
        system_messages.extend(self._build_reasoning_directives(self.strategy))

        # Tell the LLM to call our final_result() function if the task is complete
        system_messages.extend([
            "",
            "When the task is complete, provide your response in JSON format with the following structure:",
            "  {",
            "    'content': The content of the result",
            "    'status': The status of the result, @enum: success, error, partial",
            "    'metadata': Optional metadata about the result",
            "    'error': Optional error message if status is error",
            "  }",
            "If the task is not complete, continue with your analysis.",
        ])

        return system_messages

    def create_graph_from_upper_node(
        self, 
        node: ExecutionNode, 
        upper_graph: Optional[ExecutionGraph] = None
    ) -> Optional[Reasoning]:
        """Create a Reasoning graph based on an upper-level node (e.g., Plan node).
        
        This implementation creates a simple single-node graph for reasoning.
        
        Args:
            node: The upper-level node (usually a Planning node).
            upper_graph: The graph the node belongs to (optional).
            
        Returns:
            A Reasoning instance or None if creation fails.
        """
        self.info(f"Creating Reasoning graph for upper node: {node.node_id}")
        
        # Create a new reasoning graph (using Reasoning class)
        reasoning_graph = Reasoning(
            name=f"Reasoning for {node.node_id}",
            objective=node.objective  # Use the Objective object directly
        )
        
        # Create a single reasoning node based on the upper node's objective
        reasoning_node = ExecutionNode(
            node_id="REASON",  # Simple ID for the single reasoning task
            node_type=NodeType.TASK,  # Treat reasoning as a task
            objective=node.objective,  # Inherit objective
            metadata=node.metadata  # Inherit metadata
        )
        
        # Add START, reasoning node, and END
        start_node = ExecutionNode(node_id="START", node_type=NodeType.START, objective=Objective("Start Reasoning"))
        end_node = ExecutionNode(node_id="END", node_type=NodeType.END, objective=Objective("End Reasoning"))
        
        reasoning_graph.add_node(start_node)
        reasoning_graph.add_node(reasoning_node)
        reasoning_graph.add_node(end_node)
        
        # Connect nodes using ExecutionEdge objects
        reasoning_graph.add_edge(ExecutionEdge(start_node, reasoning_node))
        reasoning_graph.add_edge(ExecutionEdge(reasoning_node, end_node))
        
        return reasoning_graph
