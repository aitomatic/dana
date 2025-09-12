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
)
from .planner_executor import (
    get_planner_prompt,
    get_executor_prompt,
)
from .domain_support import (
    get_diagnostic_workflow_prompt,
)

__all__ = [
    # Reactive support prompts
    "REACTIVE_SUPPORT_SYSTEM_PROMPT",
    "get_reactive_support_prompt_all_info_provided",
    "get_reactive_support_prompt_general",
    # Simple helpful prompts
    "SIMPLE_HELPFUL_SYSTEM_PROMPT",
    # Planner executor prompts
    "get_planner_prompt",
    "get_executor_prompt",
    # Domain support prompts
    "get_diagnostic_workflow_prompt",
]
