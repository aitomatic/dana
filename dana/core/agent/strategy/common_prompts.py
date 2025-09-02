"""
Common Prompts for Agent Strategies

This module contains common prompt elements and functions that can be shared
between different agent strategies. This promotes consistency and reduces duplication.
"""

# Common function descriptions that appear in multiple strategies
COMMON_FUNCTIONS = """
AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning
"""

# Common decision framework
COMMON_DECISION_FRAMEWORK = """
DECISION: You must decide whether to:
1. SOLVE DIRECTLY: If the problem is simple enough, solve it directly and output the result
2. GENERATE DANA CODE: If the problem requires multiple steps, generate Dana code that will execute to solve it

Choose the appropriate approach and implement it. For Dana code generation, use the available functions above.
"""


# Common conversation history formatting
def format_conversation_history(context) -> str:
    """Format conversation history for inclusion in prompts."""
    if hasattr(context, "constraints") and "conversation_history" in context.constraints:
        return f"""
CONVERSATION HISTORY:
{context.constraints["conversation_history"]}

"""
    return ""


# Common problem context formatting
def format_problem_context(problem: str, context) -> str:
    """Format the basic problem context for prompts."""
    return f"""
PROBLEM: {problem}
OBJECTIVE: {getattr(context, "objective", f"Solve: {problem}")}
DEPTH: {getattr(context, "depth", 0)}
"""


# Common prompt building utilities
def build_common_prompt_base(problem: str, context, strategy_description: str, additional_functions: str = "") -> str:
    """Build a common prompt base that can be extended by specific strategies."""

    conversation_section = format_conversation_history(context)
    problem_context = format_problem_context(problem, context)

    # Combine common functions with strategy-specific ones
    all_functions = COMMON_FUNCTIONS + additional_functions

    return f"""
You are an AI agent solving problems using Dana code{strategy_description}.

{problem_context}{conversation_section}{all_functions}

{COMMON_DECISION_FRAMEWORK}

Generate Dana code or solve directly for: {problem}
"""
