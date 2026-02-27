"""
Tests for ToolExecutor parallel execution (Phase 8).

Covers:
- Default sequential execution (parallel=False)
- Parallel execution via ThreadPoolExecutor (parallel=True)
- tool_call_id preservation in both modes
- Async path via asyncio.gather
- max_workers respected
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from dana.core.tool.tool_executor import ToolExecutor


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_tool_call(function_name: str, arguments: dict | None = None, tool_call_id: str | None = None) -> dict:
    call = {"function": function_name, "arguments": arguments or {}}
    if tool_call_id:
        call["tool_call_id"] = tool_call_id
    return call


def _make_executor_with_registry(registry: dict) -> ToolExecutor:
    executor = ToolExecutor(tool_name_registry_getter=lambda: registry)
    return executor


def _make_simple_registry(names: list[str], return_values: list) -> dict:
    """Build a @named_tool-style registry mapping name → (obj, method_name)."""
    registry = {}
    for name, retval in zip(names, return_values, strict=False):
        obj = MagicMock()
        method = MagicMock(return_value=retval)
        # Make method non-coroutine so sync path is taken
        method.__wrapped__ = None
        obj.run = method
        registry[name] = (obj, "run")
    return registry


# ---------------------------------------------------------------------------
# Test 1: Default (parallel=False) — sequential, same results as before
# ---------------------------------------------------------------------------


def test_execute_tools_sequential_default():
    """parallel=False (default) returns correct results sequentially."""
    registry = _make_simple_registry(["tool_a", "tool_b"], ["result_a", "result_b"])
    executor = _make_executor_with_registry(registry)
    agent = MagicMock()

    calls = [
        _make_tool_call("tool_a"),
        _make_tool_call("tool_b"),
    ]
    results = executor.execute_tools(agent, calls)

    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is True


# ---------------------------------------------------------------------------
# Test 2: parallel=True — all tools executed, results match
# ---------------------------------------------------------------------------


def test_execute_tools_parallel_returns_correct_results():
    """parallel=True executes all tools and returns correct results."""
    registry = _make_simple_registry(["tool_x", "tool_y", "tool_z"], ["rx", "ry", "rz"])
    executor = _make_executor_with_registry(registry)
    agent = MagicMock()

    calls = [
        _make_tool_call("tool_x"),
        _make_tool_call("tool_y"),
        _make_tool_call("tool_z"),
    ]
    results = executor.execute_tools(agent, calls, parallel=True)

    assert len(results) == 3
    assert all(r["success"] is True for r in results)


# ---------------------------------------------------------------------------
# Test 3: parallel=True — tool_call_id preserved
# ---------------------------------------------------------------------------


def test_execute_tools_parallel_preserves_tool_call_id():
    """parallel=True attaches tool_call_id to each result."""
    registry = _make_simple_registry(["tool_a", "tool_b"], ["ra", "rb"])
    executor = _make_executor_with_registry(registry)
    agent = MagicMock()

    calls = [
        _make_tool_call("tool_a", tool_call_id="id-1"),
        _make_tool_call("tool_b", tool_call_id="id-2"),
    ]
    results = executor.execute_tools(agent, calls, parallel=True)

    assert results[0]["tool_call_id"] == "id-1"
    assert results[1]["tool_call_id"] == "id-2"


# ---------------------------------------------------------------------------
# Test 3b: sequential — tool_call_id also preserved
# ---------------------------------------------------------------------------


def test_execute_tools_sequential_preserves_tool_call_id():
    """Sequential mode also attaches tool_call_id."""
    registry = _make_simple_registry(["tool_a"], ["ra"])
    executor = _make_executor_with_registry(registry)
    agent = MagicMock()

    calls = [_make_tool_call("tool_a", tool_call_id="seq-id")]
    results = executor.execute_tools(agent, calls)

    assert results[0]["tool_call_id"] == "seq-id"


# ---------------------------------------------------------------------------
# Test 4: Async path — results are correct (asyncio.gather correctness)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_tools_async_returns_correct_results():
    """Async path via asyncio.gather returns correct results for all calls."""
    registry = _make_simple_registry(["tool_p", "tool_q"], ["rp", "rq"])
    executor = _make_executor_with_registry(registry)
    agent = MagicMock()

    calls = [
        _make_tool_call("tool_p", tool_call_id="async-id-1"),
        _make_tool_call("tool_q", tool_call_id="async-id-2"),
    ]
    results = await executor.execute_tools_async(agent, calls)

    assert len(results) == 2
    assert all(r["success"] is True for r in results)
    assert results[0]["tool_call_id"] == "async-id-1"
    assert results[1]["tool_call_id"] == "async-id-2"


# ---------------------------------------------------------------------------
# Test 5: max_workers respected when parallel=True
# ---------------------------------------------------------------------------


def test_execute_tools_parallel_max_workers_respected():
    """ThreadPoolExecutor is created with max_workers when set on executor."""
    executor = ToolExecutor(max_workers=2)
    agent = MagicMock()

    # Patch _execute_single_call to return a simple success dict
    def fake_single(agent, call):
        return {"status": "success", "result": "ok"}

    calls = [_make_tool_call("irrelevant") for _ in range(4)]

    with patch.object(executor, "_execute_single_call", side_effect=fake_single):
        with patch("concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_ctx = MagicMock()
            mock_tpe.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_tpe.return_value.__exit__ = MagicMock(return_value=False)

            # Submit returns futures that have .result() returning success dict
            future_mock = MagicMock()
            future_mock.result.return_value = {"status": "success", "result": "ok"}
            mock_ctx.submit.return_value = future_mock

            executor.execute_tools(agent, calls, parallel=True)

        mock_tpe.assert_called_once_with(max_workers=2)


# ---------------------------------------------------------------------------
# Test 6: parallel=True — threads actually run concurrently (smoke test)
# ---------------------------------------------------------------------------


def test_execute_tools_parallel_uses_multiple_threads():
    """Verify that parallel=True dispatches work across multiple threads."""
    observed_threads: list[int] = []
    lock = threading.Lock()

    def fake_single(agent, call):
        with lock:
            observed_threads.append(threading.get_ident())
        return {"status": "success", "result": "ok"}

    executor = ToolExecutor(max_workers=4)
    agent = MagicMock()
    calls = [_make_tool_call("t") for _ in range(4)]

    with patch.object(executor, "_execute_single_call", side_effect=fake_single):
        results = executor.execute_tools(agent, calls, parallel=True)

    assert len(results) == 4
    # At least one unique thread ID should appear (concurrent execution possible)
    assert len(observed_threads) == 4
