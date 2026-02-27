"""
Unit tests for LLMCaller Phase 7: retry, exponential backoff, and provider failover.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dana.common.llm.types import ConfigurationError, LLMError, LLMResponse, ProviderError
from dana.core.llm.llm_caller import LLMCaller, ProviderConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(content: str = "ok") -> LLMResponse:
    return LLMResponse(content=content, model="test-model")


def _make_caller(fallbacks=None, max_retries=2, base_delay=0.0) -> tuple[LLMCaller, MagicMock]:
    """Return (caller, mock_llm) with chat_response_sync pre-wired."""
    mock_llm = MagicMock()
    caller = LLMCaller(
        llm=mock_llm,
        fallback_providers=fallbacks,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    return caller, mock_llm


# ---------------------------------------------------------------------------
# Test 1: No fallbacks — single call, exception propagates directly
# ---------------------------------------------------------------------------


def test_no_fallbacks_success():
    caller, mock_llm = _make_caller()
    mock_llm.chat_response_sync.return_value = _make_response("hello")
    result = caller.call_llm([])
    assert result.content == "hello"
    mock_llm.chat_response_sync.assert_called_once()


def test_no_fallbacks_exception_propagates():
    caller, mock_llm = _make_caller()
    mock_llm.chat_response_sync.side_effect = ProviderError("rate limit exceeded")
    with pytest.raises(ProviderError):
        caller.call_llm([])
    # Called exactly once — no retry without fallbacks
    mock_llm.chat_response_sync.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: Transient error → retries with backoff → succeeds on retry
# ---------------------------------------------------------------------------


@patch("time.sleep")
def test_retry_succeeds_on_second_attempt(mock_sleep):
    caller, mock_llm = _make_caller(fallbacks=[ProviderConfig(provider="openai")], max_retries=2, base_delay=1.0)
    mock_llm.chat_response_sync.side_effect = [
        ProviderError("rate limit"),
        _make_response("retried"),
    ]

    with patch.object(LLMCaller, "_resolve_llm", return_value=mock_llm):
        result = caller.call_llm([])

    assert result.content == "retried"
    assert mock_llm.chat_response_sync.call_count == 2
    mock_sleep.assert_called_once_with(1.0)  # base_delay * 2^0


# ---------------------------------------------------------------------------
# Test 3: Primary exhausts retries → falls back to secondary → succeeds
# ---------------------------------------------------------------------------


@patch("time.sleep")
def test_failover_to_secondary_after_exhausted_retries(mock_sleep):
    fallback_cfg = ProviderConfig(provider="openai", model="gpt-4o")
    caller, primary_llm = _make_caller(fallbacks=[fallback_cfg], max_retries=1, base_delay=0.5)

    fallback_llm = MagicMock()
    fallback_llm.chat_response_sync.return_value = _make_response("fallback-ok")

    # Primary always fails transiently
    primary_llm.chat_response_sync.side_effect = ProviderError("503 service unavailable")

    with (
        patch.object(LLMCaller, "_resolve_llm", return_value=primary_llm),
        patch("dana.core.llm.llm_caller.LLM", return_value=fallback_llm),
    ):
        result = caller.call_llm([])

    assert result.content == "fallback-ok"
    # Primary called max_retries+1 times, fallback called once
    assert primary_llm.chat_response_sync.call_count == 2  # attempt 0 + 1 retry
    fallback_llm.chat_response_sync.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: Permanent error → no retry, no failover, immediate raise
# ---------------------------------------------------------------------------


@patch("time.sleep")
def test_permanent_error_no_retry_no_failover(mock_sleep):
    caller, mock_llm = _make_caller(fallbacks=[ProviderConfig(provider="openai")], max_retries=2)
    mock_llm.chat_response_sync.side_effect = ConfigurationError("bad api key")

    with patch.object(LLMCaller, "_resolve_llm", return_value=mock_llm):
        with pytest.raises(ConfigurationError):
            caller.call_llm([])

    mock_llm.chat_response_sync.assert_called_once()
    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: All providers fail → raises last exception
# ---------------------------------------------------------------------------


@patch("time.sleep")
def test_all_providers_fail_raises_last_exception(mock_sleep):
    """When all providers fail transiently, the last exception is re-raised."""
    fallback_cfg = ProviderConfig(provider="openai")
    caller, primary_llm = _make_caller(fallbacks=[fallback_cfg], max_retries=0, base_delay=0.0)

    fallback_llm = MagicMock()
    # Both errors must be transient so failover is attempted
    fallback_llm.chat_response_sync.side_effect = ProviderError("rate limit on fallback")
    primary_llm.chat_response_sync.side_effect = ProviderError("rate limit on primary")

    # Patch _invoke_llm_sync: call 1 = primary (transient), call 2 = fallback (transient)
    call_count = {"n": 0}

    def fake_invoke(llm, messages):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ProviderError("rate limit on primary")
        raise ProviderError("rate limit on fallback")

    with (
        patch.object(caller, "_invoke_llm_sync", side_effect=fake_invoke),
        patch("dana.core.llm.llm_caller.LLM", return_value=fallback_llm),
    ):
        with pytest.raises(ProviderError, match="rate limit on fallback"):
            caller.call_llm([])


# ---------------------------------------------------------------------------
# Test 6: _is_transient_error classification
# ---------------------------------------------------------------------------


def test_is_transient_timeout_error():
    assert LLMCaller._is_transient_error(TimeoutError("timed out")) is True


def test_is_transient_connection_error():
    assert LLMCaller._is_transient_error(ConnectionError("refused")) is True


def test_is_transient_provider_rate_limit():
    assert LLMCaller._is_transient_error(ProviderError("rate limit exceeded")) is True


def test_is_transient_provider_429():
    assert LLMCaller._is_transient_error(ProviderError("HTTP 429")) is True


def test_is_transient_provider_overloaded():
    assert LLMCaller._is_transient_error(ProviderError("model is overloaded")) is True


def test_is_permanent_configuration_error():
    assert LLMCaller._is_transient_error(ConfigurationError("missing api key")) is False


def test_is_permanent_generic_llm_error():
    assert LLMCaller._is_transient_error(LLMError("unknown error")) is False


def test_is_permanent_provider_error_non_transient():
    # ProviderError without transient keywords is permanent (e.g. invalid model name)
    assert LLMCaller._is_transient_error(ProviderError("invalid model name")) is False


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_no_fallbacks_success():
    mock_llm = MagicMock()
    mock_llm.chat_response = AsyncMock(return_value=_make_response("async-ok"))
    caller = LLMCaller(llm=mock_llm)
    result = await caller.call_llm_async([])
    assert result.content == "async-ok"


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_async_retry_succeeds_on_second_attempt(mock_sleep):
    mock_llm = MagicMock()
    mock_llm.chat_response = AsyncMock(
        side_effect=[
            ProviderError("rate limit"),
            _make_response("async-retried"),
        ]
    )

    caller = LLMCaller(llm=mock_llm, fallback_providers=[ProviderConfig(provider="openai")], max_retries=2, base_delay=1.0)
    with patch.object(LLMCaller, "_resolve_llm", return_value=mock_llm):
        result = await caller.call_llm_async([])

    assert result.content == "async-retried"
    assert mock_llm.chat_response.call_count == 2


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_async_permanent_error_no_retry(mock_sleep):
    mock_llm = MagicMock()
    mock_llm.chat_response = AsyncMock(side_effect=ConfigurationError("bad config"))

    caller = LLMCaller(llm=mock_llm, fallback_providers=[ProviderConfig(provider="openai")], max_retries=2)
    with patch.object(LLMCaller, "_resolve_llm", return_value=mock_llm):
        with pytest.raises(ConfigurationError):
            await caller.call_llm_async([])

    mock_llm.chat_response.assert_called_once()
    mock_sleep.assert_not_called()
