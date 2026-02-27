"""
LLMCaller — wraps the LLM invocation logic extracted from AgentRuntime.

Responsible for: lazy LLM resolution, sync and async chat calls,
retry with exponential backoff, and fallback provider support (Phase 7).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Any

import structlog

from dana.common.llm.llm import LLM
from dana.common.llm.types import (
    ConfigurationError,
    LLMError,
    LLMMessage,
    LLMResponse,
    ProviderError,
)
from dana.common.observable import observable


if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# Keywords that indicate a transient (retriable) provider error
_TRANSIENT_KEYWORDS = ("rate limit", "timeout", "5xx", "503", "502", "429", "overloaded", "down", "unavailable", "unreachable")


@dataclass
class ProviderConfig:
    """Configuration for a fallback LLM provider."""

    provider: str
    model: str | None = None
    api_key: str | None = None  # optional override
    priority: int = 0  # lower = higher priority (used for sorting fallbacks)


class LLMCaller:
    """
    Encapsulates LLM invocation for AgentRuntime.

    Parameters
    ----------
    llm:
        Pre-built LLM instance. When None, one is lazily created from
        ``provider`` / ``model`` on first call.
    model:
        Model name passed to :class:`LLM` when lazy-creating.
    provider:
        Provider name (e.g. ``"anthropic"``, ``"openai"``).
    temperature:
        Sampling temperature forwarded to the LLM call.
    max_tokens:
        Max tokens forwarded to the LLM call.
    native_tools_getter:
        Zero-argument callable that returns the current native tools list
        (or ``None``).  Called on every invocation so changes are reflected.
    agent_getter:
        Zero-argument callable that returns the current agent instance
        (or ``None``).  Used to read ``object_id``, ``agent_type``, and
        ``llm_client``.
    json_mode:
        Whether to request JSON output from the LLM.  Defaults to ``True``
        (used by DefaultRuntime / AgentRuntime).
    fallback_providers:
        Ordered list of fallback :class:`ProviderConfig` to try when the
        primary provider fails transiently.  ``None`` disables failover.
    max_retries:
        Number of retries per provider before switching to the next one.
    base_delay:
        Base delay in seconds for exponential backoff between retries.
    """

    def __init__(
        self,
        llm: LLM | None = None,
        model: str | None = None,
        provider: str = "anthropic",
        temperature: float = 0,
        max_tokens: int | None = None,
        native_tools_getter: Callable[[], list | None] | None = None,
        agent_getter: Callable[[], Any] | None = None,
        json_mode: bool = True,
        fallback_providers: list[ProviderConfig] | None = None,
        max_retries: int = 2,
        base_delay: float = 1.0,
    ) -> None:
        self._llm = llm
        self._model = model
        self._provider = provider
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._native_tools_getter = native_tools_getter or (lambda: None)
        self._agent_getter = agent_getter or (lambda: None)
        self._json_mode = json_mode
        self._fallback_providers = sorted(fallback_providers, key=lambda p: p.priority) if fallback_providers else None
        self._max_retries = max_retries
        self._base_delay = base_delay

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_llm(self, llm: LLM) -> None:
        """Replace the current LLM instance."""
        self._llm = llm

    @observable
    def call_llm(self, messages: list[LLMMessage]) -> LLMResponse:
        """Synchronous LLM call. Returns an :class:`LLMResponse`."""
        if self._fallback_providers:
            return self._call_with_failover(messages)
        return self._invoke_llm_sync(self._resolve_llm(), messages)

    @observable
    async def call_llm_async(self, messages: list[LLMMessage]) -> LLMResponse:
        """Asynchronous LLM call. Returns an :class:`LLMResponse`."""
        if self._fallback_providers:
            return await self._call_with_failover_async(messages)
        return await self._invoke_llm_async(self._resolve_llm(), messages)

    async def call_llm_stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        """Stream LLM response, yielding text chunks as strings.

        Note: Tool calls are NOT streamed — they arrive in the non-streaming
        response. Streaming is for text generation only. No failover support
        (YAGNI — keep it simple for streaming path).

        Yields:
            str: Text delta chunks as they arrive from the LLM.
        """
        llm = self._resolve_llm()
        agent = self._agent_getter()
        agent_id = agent.object_id if agent else None
        agent_type = agent.agent_type if agent else None
        async for chunk in llm.stream(messages, agent_id=agent_id, agent_type=agent_type):
            yield chunk

    # ------------------------------------------------------------------
    # Failover logic
    # ------------------------------------------------------------------

    def _call_with_failover(self, messages: list[LLMMessage]) -> LLMResponse:
        """Sync call with retry + exponential backoff + provider failover."""
        providers: list[ProviderConfig | None] = [None, *(self._fallback_providers or [])]
        last_exc: Exception | None = None

        for fallback in providers:
            llm = self._resolve_llm() if fallback is None else LLM(provider=fallback.provider, model=fallback.model)
            provider_label = self._provider if fallback is None else fallback.provider

            for attempt in range(self._max_retries + 1):
                try:
                    return self._invoke_llm_sync(llm, messages)
                except Exception as exc:
                    if not self._is_transient_error(exc):
                        raise
                    last_exc = exc
                    if attempt < self._max_retries:
                        delay = self._base_delay * (2**attempt)
                        logger.warning("llm_retry", provider=provider_label, attempt=attempt + 1, delay=delay, error=str(exc))
                        time.sleep(delay)
                    else:
                        logger.warning("llm_failover", from_provider=provider_label, error=str(exc))

        raise last_exc  # type: ignore[misc]

    async def _call_with_failover_async(self, messages: list[LLMMessage]) -> LLMResponse:
        """Async call with retry + exponential backoff + provider failover."""
        import asyncio

        providers: list[ProviderConfig | None] = [None, *(self._fallback_providers or [])]
        last_exc: Exception | None = None

        for fallback in providers:
            llm = self._resolve_llm() if fallback is None else LLM(provider=fallback.provider, model=fallback.model)
            provider_label = self._provider if fallback is None else fallback.provider

            for attempt in range(self._max_retries + 1):
                try:
                    return await self._invoke_llm_async(llm, messages)
                except Exception as exc:
                    if not self._is_transient_error(exc):
                        raise
                    last_exc = exc
                    if attempt < self._max_retries:
                        delay = self._base_delay * (2**attempt)
                        logger.warning("llm_retry", provider=provider_label, attempt=attempt + 1, delay=delay, error=str(exc))
                        await asyncio.sleep(delay)
                    else:
                        logger.warning("llm_failover", from_provider=provider_label, error=str(exc))

        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _invoke_llm_sync(self, llm: LLM, messages: list[LLMMessage]) -> LLMResponse:
        """Execute a single synchronous LLM chat call."""
        agent = self._agent_getter()
        tools = self._native_tools_getter() or None
        return llm.chat_response_sync(
            messages,
            agent_id=agent.object_id if agent else None,
            agent_type=agent.agent_type if agent else None,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tools=tools,
            json_mode=self._json_mode,
        )

    async def _invoke_llm_async(self, llm: LLM, messages: list[LLMMessage]) -> LLMResponse:
        """Execute a single asynchronous LLM chat call."""
        agent = self._agent_getter()
        tools = self._native_tools_getter() or None
        return await llm.chat_response(
            messages,
            agent_id=agent.object_id if agent else None,
            agent_type=agent.agent_type if agent else None,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tools=tools,
            json_mode=self._json_mode,
        )

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        """Return True if the error is transient and should trigger a retry."""
        if isinstance(exc, ConfigurationError):
            return False
        if isinstance(exc, TimeoutError | ConnectionError):
            return True
        if isinstance(exc, ProviderError):
            msg = str(exc).lower()
            return any(kw in msg for kw in _TRANSIENT_KEYWORDS)
        # Generic LLMError without transient keywords → permanent
        if isinstance(exc, LLMError):
            return False
        return False

    def _resolve_llm(self) -> LLM:
        """Lazy LLM resolution.

        Priority:
        1. Cached ``self._llm``
        2. Agent's ``llm_client`` attribute (set externally)
        3. Create a new :class:`LLM` from provider/model and cache it on the
           agent if one is available.
        """
        if self._llm is not None:
            return self._llm

        agent = self._agent_getter()
        if agent is not None and getattr(agent, "_llm_client", None) is not None:
            return agent.llm_client

        self._llm = LLM(provider=self._provider, model=self._model)
        if agent is not None:
            agent.llm_client = self._llm
        return self._llm
