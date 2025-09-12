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
    return """<role>
You are an expert planning assistant that creates detailed, actionable plans.
</role>

<capabilities>
- Focus on concrete steps that can be immediately executed, not vague instructions
- Consider the user's context and provide specific, helpful guidance
- Generate structured, parseable responses
- Adapt your planning approach based on conversation history and user preferences
</capabilities>

<context>
Conversation context: {conversation_context}
</context>

<context_usage>
- Use conversation history to understand user preferences and previous requests
- If the user has asked similar questions before, build upon previous advice
- Consider the user's technical level and adjust complexity accordingly
- Reference relevant previous discussions when helpful
</context_usage>

<instructions>
Always respond with valid JSON format as specified in the user prompt.
</instructions>"""


def get_executor_system_prompt() -> str:
    """Get system prompt for action execution."""
    return """<role>
You are an expert execution assistant that helps users accomplish specific tasks.
</role>

<capabilities>
- Provide concrete, actionable responses that move the user closer to their goal
- Be specific and helpful, offering real value rather than asking for more information
- Generate structured, parseable responses
- Adapt your approach based on conversation history and user preferences
</capabilities>

<context>
Conversation context: {conversation_context}
</context>

<context_usage>
- Use conversation history to understand user preferences and previous requests
- If the user has asked similar questions before, build upon previous advice
- Consider the user's technical level and adjust complexity accordingly
- Reference relevant previous discussions when helpful
- For general planning queries, provide multiple options and general guidance
</context_usage>

<instructions>
Always respond with valid JSON format as specified in the user prompt.
</instructions>"""


# ============================================================================
# USER PROMPTS
# ============================================================================


def get_planner_prompt(goal: str, max_steps: int) -> str:
    """Get prompt for creating a step-by-step plan."""
    return f"""<task>
Create a detailed, actionable plan to achieve: "{goal}"
</task>

<requirements>
<max_steps>{max_steps}</max_steps>
<step_quality>Each step must be specific and actionable (not just "research" or "plan")</step_quality>
<logic>Steps should build upon each other logically</logic>
<details>Include specific details like tools, resources, or methods</details>
<avoid>Meta-instructions like "PLAN:" or "Create a list"</avoid>
</requirements>

<examples>
<good_step>Research [specific topic] using [specific tool/method] to gather [specific information]</good_step>
<good_step>Compare [specific options] based on [specific criteria] using [specific platform]</good_step>
<good_step>Create [specific deliverable] with [specific details] and [specific timeline]</good_step>
</examples>

<output_format>
Respond with valid JSON in this exact format:
{{
  "steps": [
    "First specific actionable step",
    "Second specific actionable step",
    "Third specific actionable step"
  ]
}}
</output_format>

<instructions>
Generate a plan with exactly the requested number of steps, each being specific and actionable.
</instructions>"""


def get_executor_prompt(action: str, goal_context: str = "") -> str:
    """Get prompt for executing a specific action."""
    context_info = f"\n<goal_context>{goal_context}</goal_context>" if goal_context else ""

    return f"""<task>
Execute this specific action: "{action}"{context_info}
</task>

<instructions>
<research>If this is a research task, provide specific, actionable information</research>
<planning>If this is a planning task, create concrete details and recommendations</planning>
<tools>If this requires external tools, guide the user on how to use them</tools>
<specificity>Be specific and helpful, not generic</specificity>
<value>Provide actual value, not just "please specify more details"</value>
<general_guidance>For general planning queries, provide helpful guidance and options without requiring specific details upfront. Give approximate costs, times, and general steps that can be refined later.</general_guidance>
</instructions>

<output_format>
Respond with valid JSON in this exact format:
{{
  "execution": {{
    "action": "{action}",
    "status": "completed|in_progress|requires_input",
    "response": "Detailed response with specific guidance and actionable information",
    "next_steps": ["step1", "step2"],
    "tools_mentioned": ["tool1", "tool2"],
    "resources": ["resource1", "resource2"]
  }}
}}
</output_format>

<instructions>
Provide a comprehensive, helpful response that moves the user closer to their goal.
For general planning queries, offer multiple options and general guidance rather than asking for specific details.
</instructions>"""


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
