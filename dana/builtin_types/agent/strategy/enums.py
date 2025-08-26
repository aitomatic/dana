"""
Strategy System Enums

This module defines enums and helper functions for the agent strategy system.
"""

from enum import Enum


class PlanType(Enum):
    """Enum for different plan types."""

    DIRECT = "direct"
    CODE = "code"
    WORKFLOW = "workflow"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    MANUAL = "manual"
    INPUT = "input"


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
        if plan_type.value.upper() == value_upper:
            return plan_type

    # Try legacy format matches for backward compatibility
    if "TYPE_DIRECT" in value_upper or "DIRECT" in value_upper or "SOLUTION" in value_upper:
        return PlanType.DIRECT
    elif "TYPE_CODE" in value_upper or "CODE" in value_upper or "PYTHON" in value_upper:
        return PlanType.CODE
    elif "TYPE_WORKFLOW" in value_upper or "WORKFLOW" in value_upper or "PROCESS" in value_upper:
        return PlanType.WORKFLOW
    elif "TYPE_DELEGATE" in value_upper or "DELEGATE" in value_upper or "AGENT" in value_upper:
        return PlanType.DELEGATE
    elif "TYPE_ESCALATE" in value_upper or "ESCALATE" in value_upper or "HUMAN" in value_upper:
        return PlanType.ESCALATE
    elif "TYPE_INPUT" in value_upper or "INPUT" in value_upper or "USER" in value_upper:
        return PlanType.INPUT
    elif "TYPE_MANUAL" in value_upper or "MANUAL" in value_upper or "USER" in value_upper:
        return PlanType.MANUAL

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
    if float_val >= 0.9:
        return ConfidenceLevel.VERY_HIGH
    elif float_val >= 0.75:
        return ConfidenceLevel.HIGH
    elif float_val >= 0.45:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW
