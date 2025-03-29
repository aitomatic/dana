"""Reasoning executor implementation."""

from ..executor import Executor
from .reasoning import Reasoning
from .reasoning_strategy import ReasoningStrategy
from .reasoning_factory import ReasoningFactory
from ..execution_types import ExecutionNode, ExecutionSignal
from ..execution_context import ExecutionContext
from typing import List, Optional

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

    async def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a reasoning node.
        
        This is the bottom layer executor, so it handles the actual execution
        of reasoning tasks. For now, it simply prints out the node information.
        
        Args:
            node: The node to execute
            context: The execution context
            prev_signals: Signals from previous execution
            upper_signals: Signals from upper layer
            lower_signals: Signals from lower layer (not used in reasoning layer)
            
        Returns:
            List of execution signals
        """
        # Print node information
        print(f"Executing reasoning node: {node.node_id}")
        print(f"Node type: {node.node_type}")
        print(f"Description: {node.description}")
        print(f"Status: {node.status}")
        print(f"Metadata: {node.metadata}")
        
        # For now, just return an empty list of signals
        return []
    