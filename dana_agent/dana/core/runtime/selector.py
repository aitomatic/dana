"""
Runtime selector for automatically choosing the appropriate AgentRuntime.

This module provides RuntimeRegistry, a class-based approach to select
runtimes based on model name, provider, and other conditions.
"""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import AgentRuntime


class RuntimeRegistry:
    """
    Registry for selecting the appropriate AgentRuntime based on conditions.

    This class manages runtime registrations and selection logic.
    Use the class-level `default` instance for standard usage, or create
    custom instances for specialized scenarios.

    Usage:
        # Use the default registry
        runtime = RuntimeRegistry.select_runtime(provider="anthropic", model="claude-3")

        # Register a custom runtime
        RuntimeRegistry.get_default().register(
            MyCustomRuntime,
            provider="custom-provider",
            priority=20,
        )

        # Create a custom registry
        custom_registry = RuntimeRegistry()
        custom_registry.register(SpecialRuntime, model_pattern="special-*")
    """

    # Class-level default instance (lazily initialized)
    _default: RuntimeRegistry | None = None

    def __init__(self) -> None:
        self._rules: list[tuple[dict[str, Any], type[AgentRuntime], dict[str, Any]]] = []

    @classmethod
    def get_default(cls) -> RuntimeRegistry:
        """Get the default registry with standard runtime registrations."""
        if cls._default is None:
            cls._default = cls._create_default()
        return cls._default

    @classmethod
    def _create_default(cls) -> RuntimeRegistry:
        """Create the default registry with standard runtime registrations."""
        from .anthropic import AnthropicRuntime
        from .default import DefaultRuntime
        from .openai import OpenAIRuntime

        registry = cls()

        # Register provider-specific runtimes with higher priority
        registry.register(AnthropicRuntime, provider="anthropic", priority=10)
        registry.register(OpenAIRuntime, provider="openai", priority=10)

        # Register DefaultRuntime as the fallback for all other providers
        registry.register(DefaultRuntime, priority=0)

        return registry

    @classmethod
    def select_runtime(
        cls,
        model: str | None = None,
        provider: str = "anthropic",
        **kwargs: Any,
    ) -> AgentRuntime:
        """
        Select the appropriate runtime using the default registry.

        This is the main entry point for runtime selection.

        Args:
            model: The model name (e.g., "claude-3-opus-20240229").
            provider: The provider name (e.g., "anthropic", "openai").
            **kwargs: Additional kwargs passed to the runtime constructor.

        Returns:
            An instantiated AgentRuntime.
        """
        return cls.get_default().select(model=model, provider=provider, **kwargs)

    @classmethod
    def reset_default(cls) -> None:
        """Reset the default registry. Useful for testing."""
        cls._default = None

    def register(
        self,
        runtime_class: type[AgentRuntime],
        *,
        provider: str | list[str] | None = None,
        model_pattern: str | None = None,
        priority: int = 0,
        **default_kwargs: Any,
    ) -> RuntimeRegistry:
        """
        Register a runtime class with matching conditions.

        Args:
            runtime_class: The AgentRuntime class to instantiate when conditions match.
            provider: Match specific provider(s). None matches any provider.
            model_pattern: Glob pattern for model names (e.g., "claude-3*", "gpt-4*").
            priority: Higher priority rules are checked first. Default is 0.
            **default_kwargs: Default kwargs passed to the runtime constructor.

        Returns:
            self, for chaining.
        """
        conditions = {
            "provider": provider,
            "model_pattern": model_pattern,
            "priority": priority,
        }
        self._rules.append((conditions, runtime_class, default_kwargs))
        # Sort by priority (higher first)
        self._rules.sort(key=lambda x: -x[0].get("priority", 0))
        return self

    def select(
        self,
        model: str | None = None,
        provider: str = "anthropic",
        **kwargs: Any,
    ) -> AgentRuntime:
        """
        Select and instantiate the appropriate runtime.

        Args:
            model: The model name (e.g., "claude-3-opus-20240229").
            provider: The provider name (e.g., "anthropic", "openai").
            **kwargs: Additional kwargs passed to the runtime constructor.

        Returns:
            An instantiated AgentRuntime.
        """
        for conditions, runtime_class, default_kwargs in self._rules:
            if self._matches(conditions, model, provider):
                merged_kwargs = {**default_kwargs, **kwargs}
                return runtime_class(model=model, provider=provider, **merged_kwargs)

        # Fallback to DefaultRuntime
        from .default import DefaultRuntime

        return DefaultRuntime(model=model, provider=provider, **kwargs)

    def _matches(
        self,
        conditions: dict[str, Any],
        model: str | None,
        provider: str,
    ) -> bool:
        """Check if conditions match the given model and provider."""
        # Check provider
        cond_provider = conditions.get("provider")
        if cond_provider is not None:
            if isinstance(cond_provider, list):
                if provider not in cond_provider:
                    return False
            elif provider != cond_provider:
                return False

        # Check model pattern
        model_pattern = conditions.get("model_pattern")
        if model_pattern is not None:
            if model is None:
                return False
            if not fnmatch.fnmatch(model, model_pattern):
                return False

        return True

    @property
    def registered_runtimes(self) -> list[tuple[dict[str, Any], type[AgentRuntime]]]:
        """Return list of registered runtimes with their conditions (for debugging)."""
        return [(conditions, runtime_class) for conditions, runtime_class, _ in self._rules]
