"""Reasoning executor implementation."""

from ..executor import Executor
from .reasoning import Reasoning
from .reasoning_strategy import ReasoningStrategy
from .reasoning_factory import ReasoningFactory
from ..execution_types import ExecutionNode, ExecutionSignal
from ..execution_context import ExecutionContext
from typing import List

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
            
            # Plan node (middle level)
            if plan_node:
                print("\n  Plan Node:")
                print(f"    ID: {plan_node.node_id}")
                print(f"    Type: {plan_node.node_type}")
                print(f"    Description: {plan_node.description}")
                print(f"    Status: {plan_node.status}")
                
                # Reasoning node (bottom level)
                print("\n    Reasoning Node:")
                print(f"      ID: {node.node_id}")
                print(f"      Type: {node.node_type}")
                print(f"      Description: {node.description}")
                print(f"      Status: {node.status}")
                print(f"      Metadata: {node.metadata}")
        
        # For now, just return an empty list of signals
        return []
    