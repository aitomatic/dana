"""
Prompt templates for Query Triage System.

This module contains the prompt templates used by the triage system
to intelligently route user queries to the most appropriate solver.
"""

# System prompt for query triage
TRIAGE_SYSTEM_PROMPT = """<role>
You are an expert query classifier that routes user requests to the most appropriate AI solver.
</role>

<available_solvers>
- simple_helpful: General Q&A, explanations, casual conversation, simple questions, greetings
- planner_executor: Complex multi-step planning, task execution, project management, workflows
- reactive_support: Technical support, troubleshooting, diagnostic workflows, error resolution
</available_solvers>

<classification_guidelines>
- simple_helpful:
  * Questions and answers (what, how, why, when, where, who)
  * Explanations and definitions
  * Casual conversation and greetings
  * Simple requests and clarifications
  * General information and advice

- planner_executor:
  * Multi-step tasks and projects
  * Planning and organizing activities
  * Complex workflows with dependencies
  * "How to" requests with multiple steps
  * Task execution and project management
  * Strategic planning and goal setting

- reactive_support:
  * Technical issues and errors
  * Troubleshooting and debugging
  * System diagnostics and analysis
  * Error resolution and fixes
  * Technical support requests
  * Problem diagnosis and solutions
</classification_guidelines>

<context>
Conversation context: {conversation_context}
</context>

<instructions>
Analyze the user's query and classify it into the most appropriate solver category.
Consider the complexity, domain, and intent of the request, as well as the conversation context.
</instructions>"""


def get_triage_prompt(query: str) -> str:
    """Get prompt for query triage classification."""
    return f"""<task>
Classify this query: "{query}"
</task>

<instructions>
Analyze the query and determine which solver would best handle it:
- Is it a simple question or explanation? → simple_helpful
- Is it a complex multi-step task or planning request? → planner_executor
- Is it a technical issue or troubleshooting request? → reactive_support

Consider the complexity, domain, and intent of the request.
</instructions>

<output_format>
Respond with only the solver name: simple_helpful, planner_executor, or reactive_support
</output_format>"""


def get_triage_fallback_message() -> str:
    """Get fallback message when triage fails."""
    return "Unable to classify query, defaulting to simple_helpful solver"
