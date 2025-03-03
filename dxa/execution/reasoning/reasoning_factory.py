"""Factory for creating reasoning patterns."""

from typing import Optional, Any, cast

from ..execution_types import ExecutionNode, Objective
from .reasoning import Reasoning
from .reasoning_strategy import ReasoningStrategy
from ..execution_factory import ExecutionFactory

class ReasoningFactory(ExecutionFactory):
    """Creates reasoning pattern instances."""
    
    # Override class variables
    graph_class = Reasoning
    strategy_class = ReasoningStrategy
    
    @classmethod
    def create_reasoning_strategy(cls, node: ExecutionNode, context: Any = None) -> ReasoningStrategy:
        """Select appropriate reasoning strategy based on node metadata or context."""
        # Check if node has explicit reasoning strategy in metadata
        if "reasoning" in node.metadata:
            strategy_name = node.metadata["reasoning"].upper()
            try:
                return ReasoningStrategy[strategy_name]
            except KeyError:
                pass  # Invalid strategy name, fallback to auto-selection
        
        return cls._select_auto_strategy(node, context)
    
    @classmethod
    def _select_auto_strategy(cls, node: ExecutionNode, context: Any = None) -> ReasoningStrategy:
        """Select appropriate reasoning strategy based on node content and context."""
        return cls.select_strategy_from_description(
            node.description, 
            ReasoningStrategy.DEFAULT
        )
    
    @classmethod
    def create_reasoning(
        cls, 
        objective: Objective, 
        strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT
    ) -> Reasoning:
        """Create a reasoning instance with the specified strategy."""
        reasoning = cls.create_minimal_graph(objective)
        
        # Add strategy to reasoning metadata
        reasoning.metadata["strategy"] = strategy.value
        
        return cast(Reasoning, reasoning)
        
    @classmethod
    def create_minimal_reasoning(cls, objective: Optional[Objective] = None) -> Reasoning:
        """Create a minimal reasoning with just START and END nodes."""
        return cast(Reasoning, cls.create_minimal_graph(objective))