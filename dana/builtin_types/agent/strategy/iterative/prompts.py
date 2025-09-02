"""
Prompts for Iterative Strategy

This module contains all the prompt templates used by the IterativeStrategy
for building LLM analysis prompts. These prompts are designed to guide the LLM
in generating appropriate Dana code for iterative problem solving.
"""

# Analysis prompt template for iterative problem solving
ANALYSIS_PROMPT_TEMPLATE = """
You are an AI agent solving problems using Dana code through iterative refinement.

PROBLEM: {problem}
OBJECTIVE: {objective}
DEPTH: {depth}

{conversation_section}AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.iterate(improvement_plan): Plan the next iteration
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning

DECISION: You must decide whether to:
1. SOLVE DIRECTLY: If the problem is simple enough, solve it directly and output the result
2. GENERATE DANA CODE: If the problem requires iterative refinement, generate Dana code that will execute step by step

ITERATIVE STRATEGY (if generating Dana code):
- Break down the problem into manageable steps
- Execute each step and evaluate results
- Use agent.iterate() to plan improvements
- Continue until the problem is solved or max iterations reached

Choose the appropriate approach and implement it. For Dana code generation, use the available functions above.

Generate Dana code or solve directly for: {problem}
"""

# Strategy-specific functions for iterative strategy
ITERATIVE_FUNCTIONS = """
- agent.iterate(improvement_plan): Plan the next iteration
"""

# Strategy description
STRATEGY_DESCRIPTION = " through iterative refinement"

# Iterative strategy specific guidance
ITERATIVE_STRATEGY_GUIDANCE = """
ITERATIVE STRATEGY (if generating Dana code):
- Break down the problem into manageable steps
- Execute each step and evaluate results
- Use agent.iterate() to plan improvements
- Continue until the problem is solved or max iterations reached
"""

# System message for LLM calls
SYSTEM_MESSAGE = "You are an AI agent solving problems using iterative refinement."


# Function to build the analysis prompt with proper formatting
def build_analysis_prompt(problem: str, context) -> str:
    """Build the LLM analysis prompt for iterative problem solving."""

    # Include conversation history if available
    conversation_section = ""
    if hasattr(context, "constraints") and "conversation_history" in context.constraints:
        conversation_section = f"""
CONVERSATION HISTORY:
{context.constraints["conversation_history"]}

"""

    return ANALYSIS_PROMPT_TEMPLATE.format(
        problem=problem,
        objective=getattr(context, "objective", f"Solve: {problem}"),
        depth=getattr(context, "depth", 0),
        conversation_section=conversation_section,
    )
