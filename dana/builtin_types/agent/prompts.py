"""
Agent System Prompt Templates.

This module contains all prompt templates used by the agent system,
organized by category and purpose. All prompts use YAML format for
consistency and structured communication with LLMs.
"""

from typing import Any


# ============================================================================
# AGENT DESCRIPTION PROMPTS
# ============================================================================


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
    Build a natural language description of the agent for LLM prompts.

    Args:
        name: The agent's name
        personality: Agent's personality traits
        expertise: Agent's areas of expertise
        background: Agent's background information
        goals: Agent's goals and objectives
        style: Agent's communication style
        **kwargs: Additional characteristics as field_name=field_value

    Returns:
        A natural language description string for the agent
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
# PROBLEM ANALYSIS PROMPTS
# ============================================================================


def create_analysis_prompt(task: str, context: Any = None) -> str:
    """
    Create a prompt for analyzing a problem and determining the best plan.

    Args:
        task: The problem or task to analyze
        context: Additional context for the problem

    Returns:
        A YAML-formatted prompt string for problem analysis
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
# DIRECT SOLUTION PROMPTS
# ============================================================================


def create_direct_solution_prompt(problem: str, context: str | None = None) -> str:
    """
    Create a prompt for direct problem solving.

    Args:
        problem: The problem to solve directly
        context: Additional context for the problem

    Returns:
        A YAML-formatted prompt string for direct solving
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
# FALLBACK RESPONSE TEMPLATES
# ============================================================================


class FallbackResponses:
    """Collection of fallback response templates for when LLM is unavailable."""

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
        "I can assist with problem analysis, solution planning, code generation, " "workflow design, and more. How can I help you today?"
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
# PROMPT CONFIGURATION
# ============================================================================


class PromptConfig:
    """Configuration settings for prompts."""

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
# UTILITY FUNCTIONS
# ============================================================================


def format_yaml_prompt(content: str, task: dict, configuration: dict) -> str:
    """
    Format a complete YAML prompt with content, task, and configuration.

    Args:
        content: The main instruction content
        task: Task details as a dictionary
        configuration: Configuration settings as a dictionary

    Returns:
        A properly formatted YAML prompt string
    """
    import yaml

    prompt_dict = {"content": content, "task": task, "configuration": configuration}

    # Use yaml.dump for consistent formatting, then wrap in code block
    yaml_content = yaml.dump(prompt_dict, default_flow_style=False, sort_keys=False)
    return f"```yaml\n{yaml_content}```"


def extract_yaml_content(text: str) -> str:
    """
    Extract YAML content from text, handling code block wrappers.

    Args:
        text: Text potentially containing YAML in code blocks

    Returns:
        Extracted YAML content as a string
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

    Args:
        code: Code string potentially wrapped in markdown code blocks

    Returns:
        Clean code without markdown markers
    """
    # Remove ```python, ```py, ```, etc. from the beginning
    lines = code.strip().split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    # Remove trailing ``` if present
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()
