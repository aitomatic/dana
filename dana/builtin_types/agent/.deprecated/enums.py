"""
Enums for Agent system to replace string constants with type-safe enums.

This module defines enums for approach types, workflow states, and other
agent-related constants to improve type safety and code maintainability.
"""

from enum import Enum


class PlanType(Enum):
    """Enum for different approach types in agent problem solving."""

    TYPE_DIRECT = "TYPE_DIRECT"
    TYPE_CODE = "TYPE_CODE"
    TYPE_WORKFLOW = "TYPE_WORKFLOW"
    TYPE_INPUT = "TYPE_INPUT"
    TYPE_DELEGATE = "TYPE_DELEGATE"
    TYPE_ESCALATE = "TYPE_ESCALATE"

    def __str__(self) -> str:
        """Return string representation for easy comparison and logging."""
        return self.value


class ProblemComplexity(Enum):
    """Enum for problem complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"

    def __str__(self) -> str:
        return self.value


class ConfidenceLevel(Enum):
    """Enum for confidence levels in agent decisions."""

    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

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
        if plan_type.value == value_upper:
            return plan_type

    # Try partial matches for flexibility
    if "DIRECT" in value_upper or "SOLUTION" in value_upper:
        return PlanType.TYPE_DIRECT
    elif "PYTHON" in value_upper or "CODE" in value_upper:
        return PlanType.TYPE_CODE
    elif "WORKFLOW" in value_upper or "PROCESS" in value_upper:
        return PlanType.TYPE_WORKFLOW
    elif "DELEGATE" in value_upper or "AGENT" in value_upper:
        return PlanType.TYPE_DELEGATE
    elif "INPUT" in value_upper or "USER" in value_upper:
        return PlanType.TYPE_INPUT
    elif "ESCALATE" in value_upper or "HUMAN" in value_upper:
        return PlanType.ESCALATE

    # Default fallback
    return PlanType.TYPE_DIRECT


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
    if float_val >= 0.9:
        return ConfidenceLevel.VERY_HIGH
    elif float_val >= 0.75:
        return ConfidenceLevel.HIGH
    elif float_val >= 0.45:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW
