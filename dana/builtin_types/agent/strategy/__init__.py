"""
Agent Strategy System

This module provides different strategies for agent problem solving.
Each strategy implements a different approach to selecting and executing
solution methods.
"""

from typing import Any

# Import base classes and core functionality
from .base import BaseStrategy

# Import strategy implementations
# Enums removed as they're not used in simplified system
from .iterative.iterative_strategy import IterativeStrategy
from .recursive.recursive_strategy import RecursiveStrategy

# Registry of all available strategies
AVAILABLE_STRATEGIES = [
    RecursiveStrategy(),
    IterativeStrategy(),
]


def get_strategy_by_name(name: str) -> BaseStrategy | None:
    """Get strategy by name."""
    for strategy in AVAILABLE_STRATEGIES:
        if strategy.name == name:
            return strategy
    return None


def select_best_strategy(problem: str, context: Any = None) -> BaseStrategy:
    """Select the best strategy for the given problem."""
    from dana.builtin_types.agent.context import ProblemContext

    # Create default context if none provided
    if context is None:
        context = ProblemContext(problem_statement=problem, objective=f"Solve: {problem}", original_problem=problem, depth=0)

    best_strategy = None

    for strategy in AVAILABLE_STRATEGIES:
        if strategy.can_handle(problem, context):
            best_strategy = strategy
            break

    # Fallback to recursive if no strategy is confident
    return best_strategy or RecursiveStrategy()


__all__ = [
    "BaseStrategy",
    "RecursiveStrategy",
    "IterativeStrategy",
    "get_strategy_by_name",
    "select_best_strategy",
]
