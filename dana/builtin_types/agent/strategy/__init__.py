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
from .enums import (
    ConfidenceLevel,
    PlanType,
    ProblemComplexity,
    parse_complexity,
    parse_confidence,
    parse_plan_type,
)
from .iterative import IterativeStrategy
from .plan import StrategyPlan
from .recursive import RecursiveStrategy

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


def select_best_strategy(problem: str, context: dict[str, Any] | None = None) -> BaseStrategy:
    """Select the best strategy for the given problem."""
    best_strategy = None
    best_score = 0.0

    for strategy in AVAILABLE_STRATEGIES:
        score = strategy.can_handle(problem, context)
        if score > best_score:
            best_score = score
            best_strategy = strategy

    # Fallback to recursive if no strategy is confident
    return best_strategy or RecursiveStrategy()


__all__ = [
    "BaseStrategy",
    "StrategyPlan",
    "PlanType",
    "ProblemComplexity",
    "ConfidenceLevel",
    "parse_plan_type",
    "parse_complexity",
    "parse_confidence",
    "RecursiveStrategy",
    "IterativeStrategy",
    "get_strategy_by_name",
    "select_best_strategy",
]
