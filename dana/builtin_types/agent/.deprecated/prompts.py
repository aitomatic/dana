"""
Agent System Prompt Templates.

This module contains all prompt templates used by the agent system,
organized by category and purpose. All prompts use YAML format for
consistency and structured communication with LLMs.

RECURSIVE HIERARCHICAL PLANNING:
===============================

The agent system implements automatic, dynamic hierarchical planning through
a recursive relationship between agent.solve() and workflow.execute():

1. agent.solve() → workflow.execute():
   - agent.solve() analyzes problems and can generate WORKFLOW plans
   - When a WORKFLOW plan is selected, agent.solve() calls workflow.execute()
   - workflow.execute() orchestrates multi-step processes using the workflow definition

2. workflow.execute() → agent.solve():
   - workflow.execute() encounters complex sub-problems during execution
   - For each sub-problem, workflow.execute() calls agent.solve() recursively
   - agent.solve() analyzes the sub-problem and may generate its own sub-workflows

3. Automatic Hierarchical Planning:
   - This creates a tree of nested problem-solving and workflow execution
   - High-level workflows break down into lower-level agent solutions
   - Lower-level solutions can spawn their own workflows for complex sub-tasks
   - The system automatically determines the appropriate level of abstraction
   - No manual hierarchy definition required - emerges dynamically from problem complexity

4. Benefits:
   - Scalable problem decomposition without human intervention
   - Automatic handling of varying complexity levels
   - Dynamic resource allocation based on problem requirements
   - Seamless integration of planning and execution phases
"""

from typing import Any

# ============================================================================
# AGENT.SOLVE() - PROBLEM ANALYSIS PROMPTS (MOST SIGNIFICANT)
# ============================================================================

"""
PROBLEM ANALYSIS PROMPTS:
=========================

Function: agent.solve() → _create_plan() → create_analysis_prompt()
Control Flow: User problem → YAML analysis prompt → LLM reasoning → plan type selection
Prompts Used: create_analysis_prompt() → LLM → _parse_analysis()

Plan Types & Routing:
- TYPE_DIRECT → return solution directly (simple problems)
- TYPE_CODE → _execute_python() (code generation)
- TYPE_WORKFLOW → _execute_workflow() (multi-step processes)
- TYPE_DELEGATE → _delegate_to_agent() (specialized expertise)
- TYPE_INPUT → _input_from_user() (user input)
- TYPE_ESCALATE → _escalate_to_human() (human intervention)
"""


def create_analysis_prompt(task: str, context: Any = None) -> str:
    """
    Create YAML prompt for problem analysis and plan type determination.

    USED BY: agent.solve() → _create_plan()
    WHEN: Initial problem analysis to determine solution approach

    Returns YAML prompt that guides LLM to choose optimal plan type and provide structured solution.
    """
    return f"""```yaml
content: |
  You are an AI agent specialized in problem analysis and solution planning.
  Analyze the given problem and determine the best plan.

task:
  problem: "{task}"
  context: {context}

requirements:
  - Choose the best plan from: TYPE_DIRECT, TYPE_CODE, TYPE_WORKFLOW, TYPE_DELEGATE, TYPE_ESCALATE
  - Provide the actual solution, code, or action
  - Do not use tool-calling
  - Return response in YAML format

plan_types:
  TYPE_DIRECT: Simple problems (arithmetic, facts) - provide direct answer
  TYPE_CODE: Code generation problems - provide executable Python code
  TYPE_WORKFLOW: Complex multi-step processes - provide workflow definition
  TYPE_DELEGATE: Specialized agent problems - specify which agent to handle
  TYPE_INPUT: User input required - ask user for input
  TYPE_ESCALATE: Too complex for current capabilities - explain why human needed

response_formats:
  - plan: TYPE_DIRECT
    solution: "Provide direct answer, calculation result, or factual information"
  - plan: TYPE_CODE
    solution: |
      ```python
      # Complete, executable Python code with imports and comments
      ```
  - plan: TYPE_WORKFLOW
    solution: |
      workflow:
        name: "Workflow Name"
        steps:
        - step: 1
            action: "action_name"
            objective: "What is the objective of this step?"
  - plan: TYPE_INPUT
    solution: |
      input:
        question: "What is the input required?"
        type: "string|number|boolean|list|dict"
  - plan: TYPE_DELEGATE
    solution: |
      delegation:
        target_agent: "Agent Name/Type"
        problem_description: "What to delegate"
  - plan: TYPE_ESCALATE
    solution: |
      escalation:
        reason: "Why human intervention is needed"
        urgency: "HIGH|MEDIUM|LOW"

configuration:
  format: yaml
  max_tokens: 1500
```"""


# ============================================================================
# AGENT.SOLVE() - MANUAL SOLUTION PROMPTS (fallback)
# ============================================================================

"""
MANUAL SOLUTION PROMPTS:
========================

Function: agent.solve() → return solution manually → create_manual_solution_prompt()
Control Flow: Problem routing → manual solution → LLM reasoning → formatted answer
Prompts Used: create_manual_solution_prompt() → LLM → "Manual solution: {answer}"

Fallback Scenarios:
- Plan parsing fails → _execute_plan() → _solve_manually()
- Unknown dict plan type → _route_dict() → _solve_manually()
- String plan not escalation/delegation → _route_string() → _solve_manually()
"""


def create_manual_solution_prompt(problem: str, context: str | None = None) -> str:
    """
    Create YAML prompt for manual problem solving.

    USED BY: agent.solve() → _solve_manually()
    WHEN: Fallback when plan parsing fails or for simple problems

    Returns YAML prompt for straightforward problem solving.
    """
    context_str = context if context else "{}"

    return f"""```yaml
content: |
  You are an AI agent solving problems manually.
  Provide a clear, actionable solution to the given problem.

task:
  problem: "{problem}"
  context: {context_str}

configuration:
  format: yaml
  temperature: 0.7
  max_tokens: 800
```"""


# ============================================================================
# AGENT.CHAT() - AGENT DESCRIPTION PROMPTS
# ============================================================================

"""
AGENT DESCRIPTION PROMPTS:
==========================

Function: agent.chat() → _build_agent_description() → build_agent_description()
Control Flow: Agent instance fields → natural language description → LLM system prompt
Prompts Used: build_agent_description() → LLM system prompt in _chat_impl()

Data Flow:
1. Agent instance has _values dict with field data
2. implementations.py extracts personality, expertise, etc.
3. This function converts structured data to natural language
4. Result used as system prompt in _chat_impl() method
5. LLM uses description to maintain agent persona
"""


def build_agent_description(
    name: str,
    personality: str | None = None,
    expertise: str | None = None,
    background: str | None = None,
    goals: str | None = None,
    style: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Build natural language description of agent for LLM system prompts.

    USED BY: agent.chat() → _build_agent_description()
    WHEN: Creating system prompt for conversational interactions

    Returns natural language description that serves as LLM system prompt.
    """
    description = f"You are {name}."

    characteristics = []
    if personality:
        characteristics.append(f"Your personality is {personality}")
    if expertise:
        characteristics.append(f"Your expertise includes {expertise}")
    if background:
        characteristics.append(f"Your background is {background}")
    if goals:
        characteristics.append(f"Your goals are {goals}")
    if style:
        characteristics.append(f"Your communication style is {style}")

    # Add any additional characteristics
    for field_name, field_value in kwargs.items():
        if field_value and field_name not in ["config", "_conversation_memory", "_llm_resource_instance", "_memory"]:
            characteristics.append(f"Your {field_name} is {field_value}")

    if characteristics:
        description += " " + " ".join(characteristics) + "."

    # Add general instructions for natural conversation
    description += " You should respond naturally and conversationally, as if you're having a friendly chat. Be helpful, engaging, and authentic in your responses."

    return description


# ============================================================================
# AGENT.CHAT() - FALLBACK RESPONSE TEMPLATES (when LLM unavailable)
# ============================================================================

"""
FALLBACK RESPONSE TEMPLATES:
============================

Function: agent.chat() → _generate_fallback_response() → FallbackResponses methods
Control Flow: Message analysis → response type detection → template selection → formatted response
Prompts Used: FallbackResponses.get_*() methods → YAML formatted response

Response Type Mapping:
- Greetings ("hello", "hi") → get_greeting()
- Identity queries ("who are you") → get_name_inquiry()
- Help requests ("help", "what can you do") → get_help()
- Memory queries ("remember", "recall") → Memory-based response logic
- Default/unknown → get_default() or get_error()

Purpose: Ensures agents remain functional when LLM resources are unavailable.
"""


class FallbackResponses:
    """
    Fallback response templates for when LLM is unavailable.

    USED BY: agent.chat() → _generate_fallback_response()
    WHEN: LLM is unavailable or fails to respond

    Provides graceful degradation when LLM resources are unavailable.
    """

    GREETING_RESPONSES = [
        "Hello! I'm {name}, ready to assist you.",
        "Hi there! {name} here, how can I help?",
        "Greetings! I'm {name}, at your service.",
    ]

    NAME_INQUIRY_RESPONSE = "I'm {name}, an AI agent here to help you with your tasks."

    HELP_RESPONSE = (
        "I'm {name}, and I can help you with various tasks including problem solving, "
        "code generation, and workflow creation. What would you like to work on?"
    )

    CAPABILITY_RESPONSE = (
        "I can assist with problem analysis, solution planning, code generation, workflow design, and more. How can I help you today?"
    )

    THANKS_RESPONSE = "You're welcome! Let me know if there's anything else I can help with."

    GOODBYE_RESPONSE = "Goodbye! Feel free to return if you need any assistance."

    DEFAULT_RESPONSE = (
        "I understand you're asking about '{topic}'. While I'm currently in fallback mode, "
        "I'm designed to help with problem solving, analysis, and planning. "
        "Please ensure I'm properly connected to an LLM for the best experience."
    )

    ERROR_RESPONSE = (
        "I apologize, but I'm currently unable to provide a full response as I'm not connected "
        "to an LLM service. I'm {name}, and once properly configured, I'll be able to help you "
        "with your request about '{topic}'."
    )

    @classmethod
    def get_greeting(cls, agent_name: str, index: int = 0) -> str:
        """Get a greeting response with agent name."""
        responses = cls.GREETING_RESPONSES
        return responses[index % len(responses)].format(name=agent_name)

    @classmethod
    def get_name_inquiry(cls, agent_name: str) -> str:
        """Get response for name inquiry."""
        return cls.NAME_INQUIRY_RESPONSE.format(name=agent_name)

    @classmethod
    def get_help(cls, agent_name: str) -> str:
        """Get help response."""
        return cls.HELP_RESPONSE.format(name=agent_name)

    @classmethod
    def get_default(cls, agent_name: str, topic: str) -> str:
        """Get default fallback response."""
        return cls.DEFAULT_RESPONSE.format(name=agent_name, topic=topic)

    @classmethod
    def get_error(cls, agent_name: str, topic: str) -> str:
        """Get error fallback response."""
        return cls.ERROR_RESPONSE.format(name=agent_name, topic=topic)


# ============================================================================
# UTILITY - UTILITY FUNCTIONS (LEAST SIGNIFICANT - helper functions)
# ============================================================================

"""
UTILITY FUNCTIONS:
==================

Function: Various agent methods → utility functions
Control Flow: Raw LLM response → processing → structured data
Prompts Used: Helper functions for prompt processing and YAML handling

- extract_yaml_content(): agent.solve() → _parse_analysis()
- clean_code_block(): agent.solve() → _complete_plan()
- format_yaml_prompt(): General prompt formatting utility
"""


def format_yaml_prompt(content: str, task: dict, configuration: dict) -> str:
    """
    Format complete YAML prompt with content, task, and configuration.

    USED BY: General utility for prompt formatting
    WHEN: Creating structured YAML prompts with consistent formatting
    """
    import yaml

    prompt_dict = {"content": content, "task": task, "configuration": configuration}

    # Use yaml.dump for consistent formatting, then wrap in code block
    yaml_content = yaml.dump(prompt_dict, default_flow_style=False, sort_keys=False)
    return f"```yaml\n{yaml_content}```"


def extract_yaml_content(text: str) -> str:
    """
    Extract YAML content from text, handling code block wrappers.

    USED BY: agent.solve() → _parse_analysis()
    WHEN: Processing LLM responses to extract structured YAML data

    Handles ```yaml...``` blocks (preferred) and generic ```...``` blocks (fallback).
    """
    if "```yaml" in text:
        # Split on ```yaml and get everything after it
        parts = text.split("```yaml", 1)
        if len(parts) > 1:
            content = parts[1]
            # Find the closing ``` to get the complete YAML block
            if "```" in content:
                yaml_parts = content.split("```")
                if len(yaml_parts) > 1:
                    return yaml_parts[0].strip()
            return content.strip()
    elif "```" in text:
        # Split on ``` and get everything after it
        parts = text.split("```", 1)
        if len(parts) > 1:
            content = parts[1]
            # Find the closing ``` to get the complete block
            if "```" in content:
                block_parts = content.split("```")
                if len(block_parts) > 1:
                    return block_parts[0].strip()
            return content.strip()
    return text.strip()


def clean_code_block(code: str) -> str:
    """
    Remove code block markers from code string.

    USED BY: agent.solve() → _complete_plan()
    WHEN: Preparing code for execution by removing markdown formatting

    Removes ```python, ```py, and ``` markers while preserving code structure.
    """
    # Remove ```python, ```py, ```, etc. from the beginning
    lines = code.strip().split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    # Remove trailing ``` if present
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()
