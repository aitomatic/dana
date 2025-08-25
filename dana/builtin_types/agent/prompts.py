"""
Agent System Prompt Templates.

This module contains all prompt templates used by the agent system,
organized by category and purpose. All prompts use YAML format for
consistency and structured communication with LLMs.
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
- DIRECT_SOLUTION → _solve_direct() (simple problems)
- PYTHON_CODE → _execute_python() (code generation)
- WORKFLOW → _execute_workflow() (multi-step processes)
- DELEGATE → _delegate_to_agent() (specialized expertise)
- ESCALATE → _escalate_to_human() (human intervention)
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
  - Choose the best plan from: DIRECT_SOLUTION, PYTHON_CODE, WORKFLOW, DELEGATE, ESCALATE
  - Provide the actual solution, code, or action
  - Return response in YAML format

plan_types:
  DIRECT_SOLUTION: For simple problems (arithmetic, facts, calculations) - provide direct answer
  PYTHON_CODE: For problems needing code generation - provide complete, executable Python code
  WORKFLOW: For complex processes requiring multiple steps - provide workflow definition
  DELEGATE: For problems needing specialized agents - specify which agent should handle this
  ESCALATE: For problems too complex for current capabilities - explain why human intervention needed

response_format:
  plan: PLAN_TYPE
  confidence: 0.95
  reasoning: Why this plan is best for this problem
  solution: The actual solution, code, or action
  details:
    complexity: SIMPLE|MODERATE|COMPLEX|CRITICAL
    estimated_duration: immediate|minutes|hours|days
    required_resources: [list, of, resources]
    risks: Any potential risks or limitations

configuration:
  format: yaml
  temperature: 0.7
  max_tokens: 1000
```"""


# ============================================================================
# AGENT.SOLVE() - DIRECT SOLUTION PROMPTS (fallback)
# ============================================================================

"""
DIRECT SOLUTION PROMPTS:
========================

Function: agent.solve() → _solve_direct() → create_direct_solution_prompt()
Control Flow: Problem routing → direct solution → LLM reasoning → formatted answer
Prompts Used: create_direct_solution_prompt() → LLM → "Direct solution: {answer}"

Fallback Scenarios:
- Plan parsing fails → _execute_plan() → _solve_direct()
- Unknown dict plan type → _route_dict() → _solve_direct()
- String plan not escalation/delegation → _route_string() → _solve_direct()
"""


def create_direct_solution_prompt(problem: str, context: str | None = None) -> str:
    """
    Create YAML prompt for direct problem solving.

    USED BY: agent.solve() → _solve_direct()
    WHEN: Fallback when plan parsing fails or for simple problems

    Returns YAML prompt for straightforward problem solving.
    """
    context_str = context if context else "{}"

    return f"""```yaml
content: |
  You are an AI agent solving problems directly.
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
# UTILITY - PROMPT CONFIGURATION (LEAST SIGNIFICANT)
# ============================================================================

"""
PROMPT CONFIGURATION:
====================

Function: Various prompt functions → PromptConfig settings
Control Flow: Prompt generation → configuration application → LLM parameters
Prompts Used: Configuration settings applied to all prompt functions

Provides configuration templates for different prompt types:
- DEFAULT_YAML_CONFIG: Base settings for all prompts
- ANALYSIS_CONFIG: Problem analysis prompts
- DIRECT_SOLUTION_CONFIG: Direct solution prompts
- CODE_GENERATION_CONFIG: Code generation tasks
- WORKFLOW_CONFIG: Workflow creation tasks
"""


class PromptConfig:
    """
    Configuration settings for prompts.

    USED BY: Various prompt functions
    WHEN: Setting LLM parameters for different prompt types
    """

    # Default YAML configuration
    DEFAULT_YAML_CONFIG = {"format": "yaml", "temperature": 0.7, "max_tokens": 1000}

    # Analysis prompt configuration
    ANALYSIS_CONFIG = {"format": "yaml", "temperature": 0.7, "max_tokens": 1000}

    # Direct solution configuration
    DIRECT_SOLUTION_CONFIG = {"format": "yaml", "temperature": 0.7, "max_tokens": 800}

    # Code generation configuration
    CODE_GENERATION_CONFIG = {
        "format": "yaml",
        "temperature": 0.5,  # Lower temperature for more deterministic code
        "max_tokens": 1500,
    }

    # Workflow configuration
    WORKFLOW_CONFIG = {"format": "yaml", "temperature": 0.6, "max_tokens": 1200}


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
