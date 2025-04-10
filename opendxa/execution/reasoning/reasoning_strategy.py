"""Reasoning strategies."""

from enum import Enum

class ReasoningStrategy(Enum):
    """Reasoning strategies."""
    DEFAULT = "CHAIN_OF_THOUGHT"
    CHAIN_OF_THOUGHT = "CHAIN_OF_THOUGHT"  # Step-by-step reasoning (default)
    TREE_OF_THOUGHT = "TREE_OF_THOUGHT"    # Branching reasoning paths
    REFLECTION = "REFLECTION"    # Self-critique and refinement
    OODA = "OODA"               # Observe-Orient-Decide-Act loop 