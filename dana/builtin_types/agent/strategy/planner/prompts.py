"""
Planner Strategy Prompt Templates.

This module contains prompt templates specific to the plan-then-execute strategy.
These prompts are used for problem analysis and plan type determination.
"""

from typing import Any

# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

default_system_message = """You are an AI agent specialized in problem analysis and solution planning.
Analyze the given problem and determine the best plan.
Do not use tool-calling under any circumstances.
"""

# ============================================================================
# PROBLEM ANALYSIS PROMPTS (MOST SIGNIFICANT)
# ============================================================================

"""
PROBLEM ANALYSIS PROMPTS:
=========================

Function: PlannerStrategy.solve() → _create_plan() → create_analysis_prompt()
Control Flow: User problem → YAML analysis prompt → LLM reasoning → plan type selection
Prompts Used: create_analysis_prompt() → LLM → _parse_analysis()

Plan Types & Routing:
- TYPE_DIRECT → return solution directly (simple problems)
- TYPE_CODE → _execute_python() (code generation)
- TYPE_WORKFLOW → _execute_workflow() (multi-step processes)
- TYPE_DELEGATE → _delegate_to_agent() (specialized expertise)
- TYPE_ESCALATE → _escalate_to_human() (human intervention)
- TYPE_INPUT → _input_from_user() (user input)
"""


def create_analysis_prompt(task: str, context: Any = None) -> str:
    """
    Create YAML prompt for problem analysis and plan type determination.

    USED BY: PlannerStrategy.solve() → _create_plan()
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
  - Choose the best plan from: TYPE_DIRECT, TYPE_CODE, TYPE_WORKFLOW, TYPE_DELEGATE, TYPE_ESCALATE, TYPE_INPUT
  - Provide the actual solution, code, or action
  - Do not use tool-calling under any circumstances
  - Return response in YAML format

plan_types:
  TYPE_DIRECT: Simple problems (arithmetic, facts) - provide direct answer
  TYPE_CODE: Code generation problems - provide executable Python code
  TYPE_WORKFLOW: Complex multi-step processes - provide workflow definition
  TYPE_DELEGATE: Specialized agent problems - specify which agent to handle
  TYPE_ESCALATE: Too complex for current capabilities - explain why human needed
  TYPE_INPUT: User input required - ask user for input

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
  - plan: TYPE_INPUT
    solution: |
      input:
        question: "What is the input required?"
        type: "string|number|boolean|list|dict"

configuration:
  format: yaml
  max_tokens: 1500
```"""


# ============================================================================
# MANUAL SOLUTION PROMPTS (fallback)
# ============================================================================

"""
MANUAL SOLUTION PROMPTS:
========================

Function: PlannerStrategy.solve() → return solution manually → create_manual_solution_prompt()
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

    USED BY: PlannerStrategy.solve() → _solve_manually()
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
# UTILITY FUNCTIONS
# ============================================================================

"""
UTILITY FUNCTIONS:
==================

Function: Various planner strategy methods → utility functions
Control Flow: Raw LLM response → processing → structured data
Prompts Used: Helper functions for prompt processing and YAML handling

- extract_yaml_content(): PlannerStrategy.solve() → _parse_analysis()
- clean_code_block(): PlannerStrategy.solve() → _complete_plan()
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

    USED BY: PlannerStrategy.solve() → _parse_analysis()
    WHEN: Processing LLM responses to extract structured YAML data

    Handles ```yaml...``` blocks (preferred) and generic ```...``` blocks (fallback).
    """
    if "```yaml" in text:
        # Split on ```yaml and get everything after it
        parts = text.split("```yaml", 1)
        if len(parts) > 1:
            content = parts[1]
            # Find the closing ``` to get the complete YAML block
            # Count opening and closing backticks to handle nested blocks
            lines = content.split("\n")
            yaml_lines = []
            backtick_count = 0

            for line in lines:
                if line.strip() == "```":
                    backtick_count += 1
                    if backtick_count == 1:  # First closing backtick
                        break
                yaml_lines.append(line)

            return "\n".join(yaml_lines).strip()
    elif "```" in text:
        # Split on ``` and get everything after it
        parts = text.split("```", 1)
        if len(parts) > 1:
            content = parts[1]
            # Find the closing ``` to get the complete block
            # Count opening and closing backticks to handle nested blocks
            lines = content.split("\n")
            block_lines = []
            backtick_count = 0

            for line in lines:
                if line.strip() == "```":
                    backtick_count += 1
                    if backtick_count == 1:  # First closing backtick
                        break
                block_lines.append(line)

            return "\n".join(block_lines).strip()
    return text.strip()


def clean_code_block(code: str) -> str:
    """
    Remove code block markers from code string.

    USED BY: PlannerStrategy.solve() → _complete_plan()
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
