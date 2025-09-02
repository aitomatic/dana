"""
Prompts for Recursive Strategy

This module contains all the prompt templates used by the RecursiveStrategy
for building LLM analysis prompts. These prompts are designed to guide the LLM
in generating appropriate Dana code for recursive problem solving.
"""

# Basic prompt template for recursive problem solving
BASIC_PROMPT_TEMPLATE = """
You are an AI agent solving problems using Dana code.
Do not use tool calls to solve the problem.

PROBLEM: {problem}
OBJECTIVE: {objective}
DEPTH: {depth}

{conversation_section}AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.solve(sub_problem, objective): Solve a sub-problem recursively
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning

DECISION: You must decide whether to:
1. SOLVE DIRECTLY: If the problem is simple enough, solve it directly and output the result
2. GENERATE DANA CODE: If the problem requires multiple steps, generate Dana code that will execute to solve it

Choose the appropriate approach and implement it. For Dana code generation, use the available functions above.

Generate Dana code or solve directly for: {problem}
"""

# Strategy-specific functions for recursive strategy
RECURSIVE_FUNCTIONS = """
- agent.solve(sub_problem, objective): Solve a sub-problem recursively
"""

# Strategy description
STRATEGY_DESCRIPTION = " through recursive problem decomposition"

# Enhanced prompt template with rich context (for future use)
ENHANCED_PROMPT_TEMPLATE = """
You are an AI agent solving problems using Dana code.

PROBLEM: {problem}
OBJECTIVE: {objective}
DEPTH: {depth}

COMPUTED CONTEXT:
- Sub-problems attempted: {complexity_indicators}
- Total execution time: {execution_time_total:.2f}s
- Error rate: {error_rate:.1%}
- Max depth reached: {max_depth_reached}

CONSTRAINTS: {constraints}
ASSUMPTIONS: {assumptions}

LEARNING FROM EXECUTION:
- Constraint violations: {constraint_violations}
- Successful patterns: {successful_patterns}
- Recent events: {recent_events}

{parent_context}

AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.solve(sub_problem, objective): Solve a sub-problem recursively
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning

RECURSION RULES:
- You can call agent.solve() for sub-problems
- Pass the workflow_instance in kwargs
- Each recursive call increases depth by 1
- Maximum depth is {max_depth}

STRATEGY GUIDANCE:
Based on the computed context above, consider:
1. What patterns have been successful so far?
2. What constraints have been violated?
3. How complex is this problem becoming?
4. What can we learn from recent actions?

Generate Dana code that solves: {problem}
"""

# System message for LLM calls
SYSTEM_MESSAGE = "You are an AI agent solving problems using Dana code."


# Function to build the basic prompt with proper formatting
def build_basic_prompt(problem: str, context) -> str:
    """Build a basic prompt when rich context is not available."""

    # Include conversation history if available
    conversation_section = ""
    if hasattr(context, "constraints") and "conversation_history" in context.constraints:
        conversation_section = f"""
CONVERSATION HISTORY:
{context.constraints["conversation_history"]}

"""

    return BASIC_PROMPT_TEMPLATE.format(
        problem=problem,
        objective=getattr(context, "objective", f"Solve: {problem}"),
        depth=getattr(context, "depth", 0),
        conversation_section=conversation_section,
    )


# Function to build the enhanced prompt with rich context
def build_enhanced_prompt(problem: str, context, computable_context=None) -> str:
    """Build an enhanced prompt with rich computable context."""

    # For now, fall back to basic prompt since we don't have rich context
    # This can be enhanced in the future when rich context is available
    return build_basic_prompt(problem, context)
