"""Reasoning executor implementation."""

from typing import List

from dxa.common.utils.resource_executor import ResourceExecutor
from ..executor import Executor
from .reasoning import Reasoning
from .reasoning_strategy import ReasoningStrategy
from .reasoning_factory import ReasoningFactory
from ..execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from ..execution_context import ExecutionContext

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

    def __init__(self, 
                 strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT):
        """Initialize the reasoning executor.
        
        Args:
            reasoning_strategy: Strategy for reasoning execution
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
        print("\nExecution Hierarchy:")
        print("===================")
        
        # Workflow node (top level)
        if workflow_node:
            print("Workflow Node:")
            print(f"  ID: {workflow_node.node_id}")
            print(f"  Type: {workflow_node.node_type}")
            print(f"  Description: {workflow_node.description}")
            print(f"  Status: {workflow_node.status}")
            workflow_obj = context.current_workflow.objective if context.current_workflow else None
            print(f"  Workflow Objective: {workflow_obj.current if workflow_obj else 'None'}")
            print(f"  Node Objective: {workflow_node.objective.current if workflow_node.objective else 'None'}")
            
            # Plan node (middle level)
            if plan_node:
                print("\n  Plan Node:")
                print(f"    ID: {plan_node.node_id}")
                print(f"    Type: {plan_node.node_type}")
                print(f"    Description: {plan_node.description}")
                print(f"    Status: {plan_node.status}")
                plan_obj = context.current_plan.objective if context.current_plan else None
                print(f"    Plan Objective: {plan_obj.current if plan_obj else 'None'}")
                print(f"    Node Objective: {plan_node.objective.current if plan_node.objective else 'None'}")
                
                # Reasoning node (bottom level)
                print("\n    Reasoning Node:")
                print(f"      ID: {node.node_id}")
                print(f"      Type: {node.node_type}")
                print(f"      Description: {node.description}")
                print(f"      Status: {node.status}")
                reasoning_obj = context.current_reasoning.objective if context.current_reasoning else None
                print(f"      Reasoning Objective: {reasoning_obj.current if reasoning_obj else 'None'}")
                print(f"      Node Objective: {node.objective.current if node.objective else 'None'}")
                print(f"      Metadata: {node.metadata}")

                # Make LLM call with the reasoning node's objective
                if context.reasoning_llm and node.objective:
                    prompt = (
                        f"Execute the reasoning task for the following objective hierarchy:\n\n"
                        f"1. Workflow Objective: "
                        f"{workflow_obj.current if workflow_obj else 'None'}\n"
                        f"2. Workflow Node within Workflow: "
                        f"{workflow_node.objective.current if workflow_node.objective else 'None'}\n"
                        f"4. Plan Node under Workflow Node Objective: "
                        f"{plan_node.objective.current if plan_node.objective else 'None'}\n"
                        f"6. Reasoning Node under Plan Node Objective: "
                        f"{node.objective.current}\n\n"
                        f"Reasoning Node Description: {node.description}\n\n"
                        f"Please provide a detailed analysis and reasoning for this task, "
                        f"ensuring your response aligns with all levels of the objective hierarchy."
                    )

                    tool_executor = ResourceExecutor()
                    tool_responses = await tool_executor.execute_resources(prompt, context)

                    if tool_responses:
                        tool_responses_text = "\n".join([
                            f"Tool: {resp['tool_name']}\nResponse: {resp['response']}"
                            for resp in tool_responses
                        ])

                        prompt = (
                            f"{prompt}\n\n"
                            f"<tool_calling>\n{tool_responses_text}\n</tool_calling>"
                        )
                        
                    response = await context.reasoning_llm.query({
                        "prompt": prompt,
                        "system_prompt": (
                            "You are executing a reasoning task. "
                            "Provide clear, logical analysis and reasoning."
                        ),
                        "parameters": {
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    })
                    
                    if response and "content" in response:
                        print("\nReasoning Result:")
                        print("================")
                        print(response["content"])
        
        # return a list of signals
        return [ExecutionSignal(
            type=ExecutionSignalType.DATA_RESULT,
            content=response["content"]
        )]

    