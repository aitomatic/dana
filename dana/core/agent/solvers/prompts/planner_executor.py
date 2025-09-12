"""
Prompt templates for PlannerExecutorSolverMixin.

This module contains all the prompt templates used by the planner executor solver
to maintain consistency and make prompts easier to modify.
"""

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


def get_executor_prompt(action: str, conversation_context: str) -> str:
    """Get prompt for executing a specific action."""
    return f"""Execute this action: "{action}"

Provide a helpful, direct response that accomplishes what the user is asking for.
Be concise but informative. If it's a question, answer it directly.
If it's a request for help, provide useful guidance.
{conversation_context}

Response:"""
