"""Reasoning executor implementation."""

from typing import List

from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from ..executor import Executor
from .reasoning import Reasoning
from .reasoning_factory import ReasoningFactory
from .reasoning_strategy import ReasoningStrategy


class ReasoningExecutor(Executor[ReasoningStrategy, Reasoning, ReasoningFactory]):
    """Executor for reasoning layer tasks.
    This executor handles the reasoning layer of execution, which is
    responsible for executing individual reasoning tasks using LLMs.
    """

    # Required class attributes
    _strategy_type = ReasoningStrategy
    _default_strategy = ReasoningStrategy.DEFAULT
    graph_class = Reasoning
    _factory_class = ReasoningFactory
    _depth = 2

    def __init__(self, strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT):
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

        # Print execution hierarchy with indentation
        self.info("\nExecution Hierarchy:")
        self.info("===================")

        # Workflow node (top level)
        if workflow_node:
            self.info("Workflow Node:")
            self.info(f"  ID: {workflow_node.node_id}")
            self.info(f"  Type: {workflow_node.node_type}")
            self.info(f"  Description: {workflow_node.description}")
            self.info(f"  Status: {workflow_node.status}")
            workflow_obj = context.current_workflow.objective if context.current_workflow else None
            self.info(f"  Workflow Objective: {workflow_obj.current if workflow_obj else 'None'}")
            self.info(f"  Node Objective: {workflow_node.objective.current if workflow_node.objective else 'None'}")

            # Plan node (middle level)
            if plan_node:
                self.info("\n  Plan Node:")
                self.info(f"    ID: {plan_node.node_id}")
                self.info(f"    Type: {plan_node.node_type}")
                self.info(f"    Description: {plan_node.description}")
                self.info(f"    Status: {plan_node.status}")
                plan_obj = context.current_plan.objective if context.current_plan else None
                self.info(f"    Plan Objective: {plan_obj.current if plan_obj else 'None'}")
                self.info(f"    Node Objective: {plan_node.objective.current if plan_node.objective else 'None'}")

                # Reasoning node (bottom level)
                self.info("\n    Reasoning Node:")
                self.info(f"      ID: {node.node_id}")
                self.info(f"      Type: {node.node_type}")
                self.info(f"      Description: {node.description}")
                self.info(f"      Status: {node.status}")
                reasoning_obj = context.current_reasoning.objective if context.current_reasoning else None
                self.info(f"      Reasoning Objective: {reasoning_obj.current if reasoning_obj else 'None'}")
                self.info(f"      Node Objective: {node.objective.current if node.objective else 'None'}")
                self.info(f"      Metadata: {node.metadata}")

                # Make LLM call with the reasoning node's objective
                if context.reasoning_llm and node.objective:
                    prompt = (
                        f"Execute the reasoning task for the following objective hierarchy:\n\n"
                        f"1. Workflow Objective: "
                        f"{workflow_obj.current if workflow_obj else 'None'}\n"
                        f"2. Workflow Node within Workflow: "
                        f"{workflow_node.objective.current if workflow_node.objective else 'None'}\n"
                        f"3. Plan Node under Workflow Node Objective: "
                        f"{plan_node.objective.current if plan_node.objective else 'None'}\n"
                        f"4. Reasoning Node under Plan Node Objective: "
                        f"{node.objective.current}\n\n"
                        f"Reasoning Node Description: {node.description}\n\n"
                        f"Please provide a detailed analysis and reasoning for this task, "
                        f"ensuring your response aligns with all levels of the objective hierarchy."
                    )

                    # Query the LLM with available resources
                    response = await context.reasoning_llm.query(request={
                        "prompt": prompt,
                        "system_prompt": "You are executing a reasoning task. Provide clear, logical analysis and reasoning.",
                        "resources": context.resources or {},
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
