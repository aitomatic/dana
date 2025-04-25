"""Reasoning executor implementation."""

from typing import List

from opendxa.base.execution.execution_context import ExecutionContext
from opendxa.base.execution.execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from opendxa.base.execution.base_executor import BaseExecutor
from opendxa.common.types import BaseRequest
from opendxa.execution.reasoning.reasoning import Reasoning
from opendxa.execution.reasoning.reasoning_factory import ReasoningFactory
from opendxa.execution.reasoning.reasoning_strategy import ReasoningStrategy


class Reasoner(BaseExecutor[ReasoningStrategy, Reasoning, ReasoningFactory]):
    """Executor for reasoning layer tasks.
    This executor handles the reasoning layer of execution, which is
    responsible for executing individual reasoning tasks using LLMs.
    """

    # Required class attributes
    _strategy_type = ReasoningStrategy
    _default_strategy = ReasoningStrategy.CHAIN_OF_THOUGHT
    graph_class = Reasoning
    _factory_class = ReasoningFactory
    _depth = 2

    def __init__(self, strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT):
        """Initialize the reasoning executor.

        Args:
            strategy: Strategy for reasoning execution
        """
        super().__init__(strategy)

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
            plan_obj = context.current_plan.objective if context.current_plan else None
            self.info(f"Plan: {plan_node.node_type} - {plan_node.description}")
            self.info(f"  Objective: {plan_obj if plan_obj else 'None'}")

            self.info(f"  Reasoning: {node.node_type} - {node.description}")
            self.info(f"    Objective: {node.objective if node.objective else 'None'}")

            # Make LLM call with the reasoning node's objective
            if context.reasoning_llm and node.objective:
                # Build the prompt using the new method
                user_messages = self._build_user_messages(context)
                system_messages = self._build_system_messages()

                # Log the prompt
                self.info("Prompt:")
                self.info("=======")
                self.info(user_messages)
                self.info(f"Resources: {context.available_resources or {}}")

                # Query the LLM with available resources
                request = BaseRequest(arguments={
                    "messages": user_messages,
                    "system_messages": system_messages,
                    "available_resources": context.available_resources or {},
                    "max_iterations": 3,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                })
                response = await context.reasoning_llm.query(request)
                response_content = response.content if response else {}

                self.info("\nReasoning Result:")
                self.info("================")
                self.info(str(response_content))

                return [ExecutionSignal(
                    type=ExecutionSignalType.DATA_RESULT if response.success else ExecutionSignalType.CONTROL_ERROR,
                    content=response_content
                )]

        # If no response was generated, return an empty result
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content={})]

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
