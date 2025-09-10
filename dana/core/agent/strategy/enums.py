"""
Strategy System Enums

This module defines enums and helper functions for the agent strategy system.
"""

from enum import Enum


class PlanType(Enum):
    """Enum for different plan types."""

    DIRECT = "direct"
    RECURSIVE = "recursive"
    ITERATIVE = "iterative"


class ProblemComplexity(Enum):
    """Enum for problem complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

    def __str__(self) -> str:
        return self.value


class ConfidenceLevel(Enum):
    """Enum for confidence levels in agent decisions."""

    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.1f}"


# Helper functions for working with enums
def parse_plan_type(value: str) -> PlanType:
    """Parse string value to PlanType enum."""
    value_upper = value.upper().strip()

    # Try direct match first
    for plan_type in PlanType:
        if plan_type.value.upper() == value_upper:
            return plan_type

    # Try legacy format matches for backward compatibility
    if "TYPE_DIRECT" in value_upper or "DIRECT" in value_upper or "SOLUTION" in value_upper:
        return PlanType.DIRECT
    elif "TYPE_RECURSIVE" in value_upper or "RECURSIVE" in value_upper or "RECURSION" in value_upper:
        return PlanType.RECURSIVE
    elif "TYPE_ITERATIVE" in value_upper or "ITERATIVE" in value_upper or "ITERATION" in value_upper:
        return PlanType.ITERATIVE

    # Default fallback
    return PlanType.DIRECT


def parse_complexity(value: str) -> ProblemComplexity:
    """Parse string value to ProblemComplexity enum."""
    value_lower = value.lower().strip()

    for complexity in ProblemComplexity:
        if complexity.value == value_lower:
            return complexity

    # Default fallback
    return ProblemComplexity.MODERATE


def parse_confidence(value: str | float) -> ConfidenceLevel:
    """Parse string or float value to ConfidenceLevel enum."""
    if isinstance(value, str):
        try:
            float_val = float(value)
        except ValueError:
            return ConfidenceLevel.MEDIUM
    else:
        float_val = value

    # Map float ranges to confidence levels
    if float_val >= 0.75:
        return ConfidenceLevel.HIGH
    elif float_val >= 0.45:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW
