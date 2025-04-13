"""Reasoning executor implementation."""

from typing import List

from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from ..base_executor import BaseExecutor
from .reasoning import Reasoning
from .reasoning_factory import ReasoningFactory
from .reasoning_strategy import ReasoningStrategy


class ReasoningExecutor(BaseExecutor[ReasoningStrategy, Reasoning, ReasoningFactory]):
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
        workflow_node = context.get_current_workflow_node()
        plan_node = context.get_current_plan_node()

        # Print concise execution hierarchy
        self.info("\nExecution Context:")
        self.info("=================")
        
        if workflow_node:
            workflow_obj = context.current_workflow.objective if context.current_workflow else None
            self.info(f"Workflow: {workflow_node.node_type} - {workflow_node.description}")
            self.info(f"  Objective: {workflow_obj.current if workflow_obj else 'None'}")

            if plan_node:
                plan_obj = context.current_plan.objective if context.current_plan else None
                self.info(f"  Plan: {plan_node.node_type} - {plan_node.description}")
                self.info(f"    Objective: {plan_obj.current if plan_obj else 'None'}")

                self.info(f"    Reasoning: {node.node_type} - {node.description}")
                self.info(f"      Objective: {node.objective.current if node.objective else 'None'}")

                # Make LLM call with the reasoning node's objective
                if context.reasoning_llm and node.objective:
                    # Build the prompt using the new method
                    prompt = self._build_llm_prompt(context)

                    # Log the prompt
                    self.info("Prompt:")
                    self.info("=======")
                    self.info(prompt)
                    self.info(f"Resources: {context.available_resources or {}}")

                    # Query the LLM with available resources

                    response = await context.reasoning_llm.query(request={
                        "prompt": prompt,
                        "system_prompt": "You are executing a reasoning task. Provide clear, logical analysis and reasoning.",
                        "available_resources": context.available_resources or {},
                        "max_iterations": 3,
                        "max_tokens": 1000,
                        "temperature": 0.7,
                    })

                    response = response or {}
                    self.info("\nReasoning Result:")
                    self.info("================")
                    self.info(str(response))

                    return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content=response)]

        # If no response was generated, return an empty result
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content={})]

    def _build_reasoning_prompt(self, strategy: ReasoningStrategy) -> List[str]:
        """Build the reasoning strategy section of the prompt.

        Args:
            strategy: The reasoning strategy to use

        Returns:
            List of strings for the reasoning strategy section
        """
        result = []
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
            "",
            "Repeat the above process exactly 3 times, or until you are confident that the task is complete and the objective is met."
        ])
        return result

    def _build_llm_prompt(self, context: ExecutionContext) -> str:
        """Build the LLM prompt for the reasoning node.

        Args:
            context: The execution context

        Returns:
            The LLM context for the reasoning node
        """
        # Get parent nodes
        workflow_node = context.get_current_workflow_node()
        plan_node = context.get_current_plan_node()

        # Get overall workflow and plan information
        workflow_obj = context.current_workflow.objective if context.current_workflow else None
        plan_obj = context.current_plan.objective if context.current_plan else None

        # Get all workflow and plan nodes
        workflow_nodes = context.current_workflow.nodes if context.current_workflow else {}
        plan_nodes = context.current_plan.nodes if context.current_plan else {}

        prompt_parts = [
            "OVERVIEW:",
            f"Overall Workflow Objective: {workflow_obj.current if workflow_obj else 'None'}",
            f"Overall Plan Objective: {plan_obj.current if plan_obj else 'None'}",
            "",
            "EXECUTION HIERARCHY:",
            "------------------",
        ]

        # Add workflow nodes sequence
        for i, workflow_node_iter in enumerate(workflow_nodes.values(), 1):
            is_current_workflow = (
                workflow_node_iter.node_id == workflow_node.node_id 
                if workflow_node_iter and workflow_node 
                else False
            )
            current_marker = " [CURRENT]" if is_current_workflow else ""
            prompt_parts.extend([
                f"{i}. {workflow_node_iter.node_type}: {workflow_node_iter.description}{current_marker}",
                f"   - Objective: {workflow_node_iter.objective.current if workflow_node_iter.objective else 'None'}",
                f"   - Status: {workflow_node_iter.status}",
            ])

            # If this is the current workflow node, show its plan sequence
            if is_current_workflow and plan_nodes:
                prompt_parts.extend([
                    "",
                    "   Plan Sequence:"
                ])
                for j, plan_node_iter in enumerate(plan_nodes.values(), 1):
                    current_plan_node = context.get_current_plan_node()
                    is_current_plan = (
                        plan_node_iter.node_id == current_plan_node.node_id 
                        if plan_node_iter and current_plan_node 
                        else False
                    )
                    current_plan_marker = " [CURRENT]" if is_current_plan else ""
                    prompt_parts.extend([
                        f"   {j}. {plan_node_iter.node_type}: {plan_node_iter.description}{current_plan_marker}",
                        f"      - Objective: {plan_node_iter.objective.current if plan_node_iter.objective else 'None'}",
                        f"      - Status: {plan_node_iter.status}",
                    ])
                prompt_parts.append("")

        prompt_parts.extend([
            "",
            "CURRENT EXECUTION CONTEXT:",
            "------------------------",
            "You are operating within a three-layer execution hierarchy: Workflow -> Plan -> Reasoning.",
            "",
            "Current Position:",
            f"- Workflow: {workflow_node.description if workflow_node else 'None'} ({workflow_node.status if workflow_node else 'None'})",
            f"- Plan: {plan_node.description if plan_node else 'None'} ({plan_node.status if plan_node else 'None'})",
        ])

        # Add reasoning strategy section
        self.debug(f"Reasoning Strategy: {self.strategy}")
        prompt_parts.extend([""])
        prompt_parts.extend(self._build_reasoning_prompt(self.strategy))

        prompt_parts.extend([
            "",
            "Your task is to execute the reasoning layer task while keeping in mind:",
            "1. The broader workflow context and its objectives",
            "2. The specific plan that this reasoning task is part of",
            "3. The immediate reasoning task requirements",
            "",
            "Ensure your response aligns with all levels of the hierarchy and contributes to achieving the overall workflow objectives."
        ])

        return "\n".join(prompt_parts)
       