"""
Protocols for prompt engineering system.

This module defines the protocols that decouple the prompt engineering
system from specific implementations, allowing for better dependency
management and testability.
"""

from typing import Protocol, runtime_checkable

from .types import DictParams


PromptTemplate = str
PromptComponent = tuple[PromptTemplate, DictParams]
PromptComponentName = str
PromptComponents = dict[PromptComponentName, PromptComponent]
SystemPromptComponents = PromptComponents
UserPromptComponents = PromptComponents
AssistantPromptComponents = PromptComponents


@runtime_checkable
class PromptsProtocol(Protocol):
    """Protocol for prompts."""

    @property
    def system_prompt_components(self) -> SystemPromptComponents | None:
        """System prompt components."""
        ...

    @property
    def user_prompt_components(self) -> UserPromptComponents | None:
        """User prompt components."""
        ...

    @property
    def assistant_prompt_components(self) -> AssistantPromptComponents | None:
        """Assistant prompt components."""
        ...

    @property
    def prt_public_description(self) -> str:
        """Public description for the object."""
        ...


class BasePrompts(PromptsProtocol):
    """Base prompts class."""

    def __init__(self):
        """Initialize the base prompts class."""
        self._system_prompt_components = None
        self._user_prompt_components = None
        self._assistant_prompt_components = None
        self._prt_public_description = "No description available"

    @property
    def system_prompt_components(self) -> SystemPromptComponents | None:
        """System prompt components."""
        if self._system_prompt_components is None:
            self._system_prompt_components = self._get_system_prompt_components()
        return self._system_prompt_components

    def _get_system_prompt_components(self) -> SystemPromptComponents | None:
        """Get system prompt components."""
        return None

    def uncache_system_prompts(self) -> None:
        """Uncache system prompt components."""
        self._system_prompt_components = None

    @property
    def user_prompt_components(self) -> UserPromptComponents | None:
        """User prompt components."""
        if self._user_prompt_components is None:
            self._user_prompt_components = self._get_user_prompt_components()
        return self._user_prompt_components

    def _get_user_prompt_components(self) -> UserPromptComponents | None:
        """Get user prompt components."""
        return None

    def uncache_user_prompt_components(self) -> None:
        """Uncache user prompt components."""
        self._user_prompt_components = None

    @property
    def assistant_prompt_components(self) -> AssistantPromptComponents | None:
        """Assistant prompt components."""
        if self._assistant_prompt_components is None:
            self._assistant_prompt_components = self._get_assistant_prompt_components()
        return self._assistant_prompt_components

    def _get_assistant_prompt_components(self) -> AssistantPromptComponents | None:
        """Get assistant prompt components."""
        return None

    def uncache_assistant_prompts(self) -> None:
        """Uncache assistant prompt components."""
        self._assistant_prompt_components = None

    def uncache_all_prompts(self) -> None:
        """Uncache prompts."""
        self.uncache_system_prompts()
        self.uncache_user_prompt_components()
        self.uncache_assistant_prompts()

    @property
    def prt_public_description(self) -> str:
        return self._prt_public_description

    def format_prompt(self, template: str, **kwargs) -> str:
        """Format a prompt template with variables."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
