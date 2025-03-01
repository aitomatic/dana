"""Factory for creating reasoning patterns."""

from typing import Any

from ..execution_types import ExecutionNode, Objective
from .reasoning import Reasoning
from .reasoning_executor import ReasoningStrategy
from ..execution_factory import ExecutionFactory

class ReasoningFactory(ExecutionFactory):
    """Creates reasoning pattern instances."""
    
    # Override class variables
    graph_class = Reasoning

    
    @classmethod
    def _select_auto_strategy(cls, node: ExecutionNode, context: Any = None) -> ReasoningStrategy:
        """Select appropriate reasoning strategy based on (Planning) node content and context."""
        # Simple heuristics for strategy selection
        description = node.description.lower()
        
        # For mathematical or logical problems, use chain of thought
        if any(keyword in description for keyword in ["calculate", "solve", "equation", "math", "logic", "proof"]):
            return ReasoningStrategy.CHAIN_OF_THOUGHT
        
        # For decision-making or situational analysis, use OODA
        if any(keyword in description for keyword in ["decide", "situation", "analyze", "assess", "evaluate"]):
            return ReasoningStrategy.OODA
        
        # For complex reasoning with multiple steps, use DANA
        if any(keyword in description for keyword in ["complex", "multi-step", "detailed", "comprehensive"]):
            return ReasoningStrategy.DANA
        
        # For PROSEA specific nodes, use PROSEA
        if node.node_id in ["ANALYZE", "PLAN", "FINALIZE"]:
            return ReasoningStrategy.PROSEA
            
        # Default to simple direct reasoning
        return ReasoningStrategy.DEFAULT
    
    @classmethod
    def create_reasoning(cls, objective: Objective,
                         strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT) -> Reasoning:
        """Create a reasoning instance with the specified strategy."""
        reasoning = Reasoning(objective)
        reasoning.metadata["strategy"] = strategy.value
        return reasoning