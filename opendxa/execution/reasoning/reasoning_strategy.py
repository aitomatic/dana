"""Reasoning strategies."""

from enum import Enum

class ReasoningStrategy(Enum):
    """Reasoning strategies."""
    DEFAULT = "DEFAULT"          # Default reasoning
    CHAIN_OF_THOUGHT = "CHAIN_OF_THOUGHT"  # Step-by-step reasoning
    TREE_OF_THOUGHT = "TREE_OF_THOUGHT"    # Branching reasoning paths
    REFLECTION = "REFLECTION"    # Self-critique and refinement 