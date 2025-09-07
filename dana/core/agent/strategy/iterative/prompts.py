"""
Prompts for Iterative Strategy

This module contains all the prompt templates used by the IterativeStrategy
for building LLM analysis prompts. These prompts are designed to guide the LLM
in generating appropriate Dana code for iterative problem solving.
"""

# Analysis prompt template for iterative problem solving
ANALYSIS_PROMPT_TEMPLATE = """<role>You are an AI agent solving problems using Dana code through iterative refinement. Do not use tool calls to solve the problem.</role>

<critical_restriction>
IMPORTANT: You must NOT use any tool calls, function calls, or external APIs. 
You can ONLY use the provided Dana functions (agent.output, agent.iterate, agent.input, agent.reason).
Do not attempt to call any other functions or tools.
</critical_restriction>

<problem>{problem}</problem>
<objective>{objective}</objective>
<depth>{depth}</depth>

{conversation_section}<functions>
<function name="agent.output" description="Specify final result when problem is solved">agent.output(result)</function>
<function name="agent.iterate" description="Plan the next iteration">agent.iterate(improvement_plan)</function>
<function name="agent.input" description="Get user input during problem solving">agent.input(prompt)</function>
<function name="agent.reason" description="Express natural language reasoning">agent.reason(thought)</function>
</functions>

<reasoning_framework>
Use the OODA loop for structured reasoning:

OBSERVE: Analyze the problem statement and identify key components, constraints, and requirements
ORIENT: Consider the context, available functions, and determine the complexity level and iteration needs
DECIDE: Choose between direct solution or iterative Dana code generation based on your analysis
ACT: Implement your chosen approach using the available functions, with iterative refinement if needed

Apply this framework to structure your thinking process.
</reasoning_framework>

<decision>
You must decide whether to:
1. SOLVE DIRECTLY: If the problem is simple enough, solve it directly and output the result
2. GENERATE DANA CODE: If the problem requires iterative refinement, generate Dana code that will execute step by step
</decision>

<iterative_strategy>
If generating Dana code:
- Break down the problem into manageable steps
- Execute each step and evaluate results
- Use agent.iterate() to plan improvements
- Continue until the problem is solved or max iterations reached
</iterative_strategy>

<instruction>Use OODA reasoning to choose the appropriate approach and implement it. For Dana code generation, use the available functions above.</instruction>

<task>Generate Dana code or solve directly for: {problem}</task>

<response_format>
You must respond with a JSON object in exactly this format:
{{
  "approach": "direct" | "dana_code",
  "reasoning": "Brief explanation of your approach",
  "dana_code": "The Dana code to execute (only if approach is 'dana_code')",
  "result": "Direct result (only if approach is 'direct')"
}}
</response_format>"""

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
        conversation_section = f"""<conversation_history>
{context.constraints["conversation_history"]}
</conversation_history>

"""

    return ANALYSIS_PROMPT_TEMPLATE.format(
        problem=problem,
        objective=getattr(context, "objective", f"Solve: {problem}"),
        depth=getattr(context, "depth", 0),
        conversation_section=conversation_section,
    )
