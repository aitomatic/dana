"""Factory for creating reasoning patterns."""

from typing import Dict, Optional, Union, Any
from pathlib import Path

from ..execution_types import ExecutionNode, Objective
from ..execution_graph import ExecutionGraph
from .reasoning import Reasoning
from .reasoning_executor import ReasoningStrategy
from ..execution_factory import ExecutionFactory
from ..execution_config import ExecutionConfig

class ReasoningConfig(ExecutionConfig):
    """Configuration for reasoning patterns."""
    
    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for configuration files."""
        return Path(__file__).parent

class ReasoningFactory(ExecutionFactory):
    """Creates reasoning pattern instances."""
    
    # Override class variables
    graph_class = Reasoning
    config_class = ReasoningConfig

    @classmethod
    def create_from_config(cls, name: str,
                           objective: Union[str, Objective],
                           role: Optional[str] = None,
                           custom_prompts: Optional[Dict[str, str]] = None) -> ExecutionGraph:
        """Create a reasoning instance by name."""
        reasoning = super().create_from_config(name, objective, role, custom_prompts)
        return reasoning
    
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