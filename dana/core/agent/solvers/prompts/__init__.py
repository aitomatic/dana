"""
Prompt templates for solver mixins.

This module contains all the prompt templates used by various solver mixins
to maintain consistency and make prompts easier to modify.
"""

from .reactive_support import (
    REACTIVE_SUPPORT_SYSTEM_PROMPT,
    get_reactive_support_prompt_all_info_provided,
    get_reactive_support_prompt_general,
)
from .simple_helpful import (
    SIMPLE_HELPFUL_SYSTEM_PROMPT,
    get_question_prompt,
    get_help_prompt,
    get_explanation_prompt,
    get_problem_solving_prompt,
)
from .planner_executor import (
    get_planner_prompt,
    get_executor_prompt,
    get_planner_system_prompt,
    get_executor_system_prompt,
    get_recursion_limit_message,
    get_math_guidance_message,
    get_math_fallback_message,
)
from .triage import (
    TRIAGE_SYSTEM_PROMPT,
    get_triage_prompt,
    get_triage_fallback_message,
)

__all__ = [
    # Reactive support prompts
    "REACTIVE_SUPPORT_SYSTEM_PROMPT",
    "get_reactive_support_prompt_all_info_provided",
    "get_reactive_support_prompt_general",
    # Simple helpful prompts
    "SIMPLE_HELPFUL_SYSTEM_PROMPT",
    "get_question_prompt",
    "get_help_prompt",
    "get_explanation_prompt",
    "get_problem_solving_prompt",
    # Planner executor prompts
    "get_planner_prompt",
    "get_executor_prompt",
    "get_planner_system_prompt",
    "get_executor_system_prompt",
    "get_recursion_limit_message",
    "get_math_guidance_message",
    "get_math_fallback_message",
    # Triage prompts
    "TRIAGE_SYSTEM_PROMPT",
    "get_triage_prompt",
    "get_triage_fallback_message",
]
