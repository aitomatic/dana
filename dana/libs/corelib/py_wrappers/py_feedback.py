"""
POET Feedback Function for Dana

This module provides a Dana function that allows users to provide feedback
on POET-enhanced function results directly from Dana code.
"""

__all__ = ["py_feedback"]

from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


def py_feedback(
    context: SandboxContext,
    result: Any,
    feedback_payload: Any,
) -> None:
    """
    Submit feedback for a POET-enhanced function result.

    This function allows Dana code to provide feedback on POET function executions
    in any format, which will be processed by the LLM-powered feedback system.

    Args:
        context: The sandbox context (automatically injected)
        result: The POETResult from a POET-enhanced function call
        feedback_payload: Feedback in any format (text, dict, number, etc.)

    Example (in Dana):
        # Basic text feedback
        feedback(result, "The prediction was excellent!")

        # Structured feedback
        feedback(result, {"rating": 4, "comment": "Good but could be faster"})

        # Numeric feedback
        feedback(result, 0.85)

        # Complex feedback
        feedback(result, {"correct": false, "expected": "positive", "reason": "Context missing"})
    """
    # Import the actual feedback implementation
    from dana.frameworks.poet.decorator import feedback as poet_feedback

    try:
        # Call the POET feedback system
        poet_feedback(result, feedback_payload)
    except Exception as e:
        # Log error but don't fail Dana execution
        from dana.common.utils.logging import DANA_LOGGER

        DANA_LOGGER.error(f"Feedback processing failed: {e}")
        # Re-raise to inform user
        raise RuntimeError(f"Feedback processing failed: {e}")
