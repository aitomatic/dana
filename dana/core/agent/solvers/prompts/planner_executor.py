"""
Prompt templates for PlannerExecutorSolver.

This module contains the essential prompt templates and user-facing messages
used by the planner executor solver.
"""

# ============================================================================
# SYSTEM PROMPTS
# ============================================================================


def get_planner_system_prompt() -> str:
    """Get system prompt for planning assistant."""
    return "You are an AI planning assistant. Create step-by-step plans to achieve goals. Be specific and actionable."


def get_executor_system_prompt() -> str:
    """Get system prompt for action execution."""
    return "You are an AI assistant that executes actions and provides helpful responses. Be direct and helpful."


# ============================================================================
# USER PROMPTS
# ============================================================================


def get_planner_prompt(goal: str, max_steps: int) -> str:
    """Get prompt for creating a step-by-step plan."""
    return f"""Create a step-by-step plan to achieve this goal: "{goal}"

Requirements:
- Maximum {max_steps} steps
- Each step should be actionable and specific
- Steps should be in logical order
- Consider dependencies between steps
- Make steps measurable and clear

Format your response as:
PLAN:
1. [Step 1]
2. [Step 2]
...

Provide a clear, actionable plan:"""


def get_executor_prompt(action: str) -> str:
    """Get prompt for executing a specific action."""
    return f"""Execute this action: "{action}"

Provide a helpful, direct response that accomplishes what the user is asking for.
Be concise but informative. If it's a question, answer it directly.
If it's a request for help, provide useful guidance.

Response:"""


# ============================================================================
# USER-FACING MESSAGES
# ============================================================================


def get_recursion_limit_message(problem: str) -> str:
    """Get message when recursion limit is reached."""
    return f"Recursion limit reached for: {problem}"


# ============================================================================
# MATH ACTION MESSAGES
# ============================================================================


def get_math_guidance_message(action: str) -> str:
    """Get guidance message for math problems."""
    return f"""I can see you're asking about a math problem: '{action}'. I can help with basic arithmetic (addition, subtraction, multiplication, division). Could you rephrase the problem in a simpler format? For example: 'What is 5 + 3?' or 'Calculate 10 * 7'."""


def get_math_fallback_message(action: str) -> str:
    """Get fallback message for math problems."""
    return f"""I can see you're asking about a math problem: '{action}'. I can help with basic arithmetic. Could you rephrase it in a simpler format? For example: 'What is 5 + 3?' or 'Calculate 10 * 7'."""
