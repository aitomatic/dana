"""
Prompts for Recursive Strategy

This module contains all the prompt templates used by the RecursiveStrategy
for building LLM analysis prompts. These prompts are designed to guide the LLM
in generating appropriate Dana code for recursive problem solving.
"""

# Shared base template components
BASE_HEADER = """<role>You are an AI agent solving problems using Dana code. Do not use tool calls to solve the problem.</role>

<critical_restriction>
IMPORTANT: You must NOT use any tool calls, function calls, or external APIs. 
You can ONLY use the provided Dana functions (agent.output, agent.solve, agent.input, agent.reason).
Do not attempt to call any other functions or tools.
</critical_restriction>

<problem>{problem}</problem>
<objective>{objective}</objective>
<depth>{depth}</depth>"""

BASE_FUNCTIONS = """<dana_syntax>
<dana name="agent.output" description="Specify final result when problem is solved">agent.output(result)</dana>
<dana name="agent.solve" description="Solve a sub-problem recursively">agent.solve(sub_problem, objective)</dana>
<dana name="agent.input" description="Get user input during problem solving">agent.input(prompt)</dana>
<dana name="agent.reason" description="Express natural language reasoning">agent.reason(thought)</dana>
</dana_syntax>"""

BASE_REASONING = """<reasoning_framework>
Use the OODA loop for structured reasoning:

OBSERVE: Analyze the problem statement and identify key components, constraints, and requirements
ORIENT: Consider the context, available functions, and determine the complexity level
DECIDE: Choose between direct solution or Dana code generation based on your analysis
ACT: Implement your chosen approach using the available functions

Apply this framework to structure your thinking process.
</reasoning_framework>"""

BASE_DECISION = """<decision>
You must decide whether to:
1. SOLVE DIRECTLY: If the problem is simple enough, solve it directly and output the result with agent.output()
2. GENERATE DANA CODE: If the problem requires multiple steps, generate Dana code that will execute to solve it
</decision>

<instruction>Use OODA reasoning to choose the appropriate approach and implement it. For Dana code generation, use the available functions above.</instruction>"""

BASE_RESPONSE_FORMAT = """<response_format>
You must respond with a JSON object in exactly this format:
{{
  "approach": "direct" | "dana_code",
  "reasoning": "Brief explanation of your approach",
  "dana_code": "The Dana code to execute (only if approach is 'dana_code')",
  "result": "Direct result (only if approach is 'direct')"
}}
</response_format>"""

# Enhanced-specific components
ENHANCED_CONTEXT = """<computed_context>
<sub_problems_attempted>{complexity_indicators}</sub_problems_attempted>
<total_execution_time>{execution_time_total:.2f}s</total_execution_time>
<error_rate>{error_rate:.1%}</error_rate>
<max_depth_reached>{max_depth_reached}</max_depth_reached>
</computed_context>

<constraints>{constraints}</constraints>
<assumptions>{assumptions}</assumptions>

<learning_from_execution>
<constraint_violations>{constraint_violations}</constraint_violations>
<successful_patterns>{successful_patterns}</successful_patterns>
<recent_events>{recent_events}</recent_events>
</learning_from_execution>

{parent_context}"""

ENHANCED_REASONING = """<reasoning_framework>
Use the OODA loop for structured reasoning:

OBSERVE: Analyze the problem statement, computed context, and identify key components, constraints, and requirements
ORIENT: Consider the context, available functions, successful patterns, and determine the complexity level
DECIDE: Choose between direct solution or Dana code generation based on your analysis and learned patterns
ACT: Implement your chosen approach using the available functions

Apply this framework to structure your thinking process.
</reasoning_framework>"""

ENHANCED_STRATEGY = """<strategy_guidance>
Based on the computed context above, consider:
1. What patterns have been successful so far?
2. What constraints have been violated?
3. How complex is this problem becoming?
4. What can we learn from recent actions?
</strategy_guidance>"""

ENHANCED_RULES = """<recursion_rules>
<rule>You can call agent.solve() for sub-problems</rule>
<rule>Pass the workflow_instance in kwargs</rule>
<rule>Each recursive call increases depth by 1</rule>
<rule>Maximum depth is {max_depth}</rule>
</recursion_rules>"""

# Basic prompt template for recursive problem solving
BASIC_PROMPT_TEMPLATE = f"""{BASE_HEADER}

{{conversation_section}}{BASE_FUNCTIONS}

{BASE_REASONING}

{BASE_DECISION}

<task>Generate Dana code or solve directly for: {{problem}}</task>

{BASE_RESPONSE_FORMAT}"""

# Strategy-specific functions for recursive strategy
RECURSIVE_FUNCTIONS = """
- agent.solve(sub_problem, objective): Solve a sub-problem recursively
"""

# Strategy description
STRATEGY_DESCRIPTION = " through recursive problem decomposition"

# Enhanced prompt template with rich context (for future use)
ENHANCED_PROMPT_TEMPLATE = f"""{BASE_HEADER}

{{conversation_section}}{ENHANCED_CONTEXT}

{BASE_FUNCTIONS}

{ENHANCED_RULES}

{ENHANCED_REASONING}

{ENHANCED_STRATEGY}

<task>Generate Dana code that solves: {{problem}}</task>

{BASE_RESPONSE_FORMAT}"""

# System message for LLM calls
SYSTEM_MESSAGE = "You are an AI agent solving problems using Python code. IMPORTANT: Do not use LLM tool calling, EVER."


# Function to build the basic prompt with proper formatting
def build_basic_prompt(problem: str, context) -> str:
    """Build a basic prompt when rich context is not available."""

    # Include conversation history if available
    conversation_section = ""
    if hasattr(context, "constraints") and "conversation_history" in context.constraints:
        conversation_section = f"""<conversation_history>
{context.constraints["conversation_history"]}
</conversation_history>

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
