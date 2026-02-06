"""Tests for thread safety in RichCLIRenderer.

Verifies that concurrent broadcasts don't corrupt RenderState and that
the threading.Lock prevents race conditions.
"""

import threading
from unittest.mock import MagicMock

from rich.console import Console

from dana.cli.rich_cli_renderer import RichCLIRenderer


class _FakeAgent:
    """Minimal fake agent for testing notify()."""

    def __init__(self, object_id: str = "test-agent") -> None:
        self.object_id = object_id
        self.agent_type = "star"
        self._star_loop_count = 0
        self.max_turns = 10


def _make_renderer() -> RichCLIRenderer:
    """Create a renderer with Live/display mocked out."""
    renderer = RichCLIRenderer(console=Console(force_terminal=False))
    renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
    renderer._stop_live = MagicMock()  # type: ignore[method-assign]
    renderer._refresh_display = MagicMock()  # type: ignore[method-assign]
    return renderer


class TestLockExists:
    """Verify the lock is properly initialized."""

    def test_renderer_has_lock(self) -> None:
        renderer = RichCLIRenderer()
        assert hasattr(renderer, "_lock")
        # Lock objects have acquire/release methods
        assert callable(getattr(renderer._lock, "acquire", None))
        assert callable(getattr(renderer._lock, "release", None))

    def test_lock_is_not_locked_initially(self) -> None:
        renderer = RichCLIRenderer()
        # Should be acquirable immediately
        acquired = renderer._lock.acquire(blocking=False)
        assert acquired is True
        renderer._lock.release()


class TestConcurrentBroadcasts:
    """Test that rapid concurrent broadcasts don't corrupt state."""

    def test_concurrent_see_broadcasts(self) -> None:
        """Multiple SEE broadcasts should not corrupt state."""
        renderer = _make_renderer()
        agent = _FakeAgent()
        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def send_see(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(agent, {"trace_percepts": {"perception": f"input-{i}"}})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=send_see, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent SEE broadcasts raised errors: {errors}"
        assert renderer.state.current_phase == "SEE"

    def test_concurrent_think_broadcasts(self) -> None:
        """Multiple THINK broadcasts should not corrupt state."""
        renderer = _make_renderer()
        agent = _FakeAgent()
        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def send_think(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(agent, {"trace_thoughts": {"response": f"chunk-{i}"}})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=send_think, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent THINK broadcasts raised errors: {errors}"
        assert renderer.state.current_phase == "THINK"

    def test_concurrent_act_broadcasts(self) -> None:
        """Multiple ACT broadcasts should not corrupt state."""
        renderer = _make_renderer()
        agent = _FakeAgent()
        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def send_act(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(
                    agent,
                    {
                        "trace_outputs": {
                            "tool_results": [
                                {"function": f"tool-{i}", "output": f"out-{i}", "exit_code": 0},
                            ],
                        },
                    },
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=send_act, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent ACT broadcasts raised errors: {errors}"
        assert renderer.state.current_phase == "ACT"
        # All 10 tool results should be present (no lost updates)
        assert len(renderer.state.current_turn_results) == 10

    def test_concurrent_mixed_broadcasts(self) -> None:
        """Mixed SEE/THINK/ACT broadcasts concurrently should not crash."""
        renderer = _make_renderer()
        agent = _FakeAgent()
        errors: list[Exception] = []
        barrier = threading.Barrier(30)

        def send_see(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(agent, {"trace_percepts": {"perception": f"p-{i}"}})
            except Exception as e:
                errors.append(e)

        def send_think(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(agent, {"trace_thoughts": {"response": f"r-{i}"}})
            except Exception as e:
                errors.append(e)

        def send_act(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(
                    agent,
                    {
                        "trace_outputs": {
                            "tool_results": [{"function": f"t-{i}", "output": "", "exit_code": 0}],
                        },
                    },
                )
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=send_see, args=(i,)))
            threads.append(threading.Thread(target=send_think, args=(i,)))
            threads.append(threading.Thread(target=send_act, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent mixed broadcasts raised errors: {errors}"


class TestConcurrentKeyboardNavigation:
    """Test that keyboard navigation is safe under concurrent access."""

    def test_concurrent_select_operations(self) -> None:
        """Concurrent select_up/select_down should not corrupt state."""
        from dana.cli.components.result_panel import ResultPanelComponent

        renderer = _make_renderer()
        # Add some results to navigate
        for i in range(5):
            renderer.state.current_turn_results.append(
                ResultPanelComponent(tool_name=f"tool-{i}", output=f"out-{i}", exit_code=0, is_recent=True)
            )
        renderer.state.selected_index = 0

        errors: list[Exception] = []
        barrier = threading.Barrier(20)

        def do_select_up() -> None:
            try:
                barrier.wait(timeout=5)
                for _ in range(10):
                    renderer.select_up()
            except Exception as e:
                errors.append(e)

        def do_select_down() -> None:
            try:
                barrier.wait(timeout=5)
                for _ in range(10):
                    renderer.select_down()
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(10):
            threads.append(threading.Thread(target=do_select_up))
            threads.append(threading.Thread(target=do_select_down))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent select ops raised errors: {errors}"
        # selected_index should be valid
        idx = renderer.state.selected_index
        assert 0 <= idx < 5, f"selected_index {idx} out of range"

    def test_concurrent_toggle_expand(self) -> None:
        """Concurrent toggle_expand should not corrupt expanded_indices."""
        from dana.cli.components.result_panel import ResultPanelComponent

        renderer = _make_renderer()
        for i in range(5):
            renderer.state.current_turn_results.append(
                ResultPanelComponent(tool_name=f"tool-{i}", output=f"out-{i}", exit_code=0, is_recent=True)
            )
        renderer.state.selected_index = 2

        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def do_toggle() -> None:
            try:
                barrier.wait(timeout=5)
                for _ in range(20):
                    renderer.toggle_expand()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_toggle) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent toggle_expand raised errors: {errors}"
        # expanded_indices should be a valid set
        assert isinstance(renderer.state.expanded_indices, set)


class TestConcurrentBroadcastsWithKeyboard:
    """Test concurrent broadcasts AND keyboard navigation."""

    def test_broadcasts_and_navigation_concurrent(self) -> None:
        """Broadcasts and keyboard ops running concurrently should not crash."""
        from dana.cli.components.result_panel import ResultPanelComponent

        renderer = _make_renderer()
        agent = _FakeAgent()
        # Pre-populate some results
        for i in range(3):
            renderer.state.current_turn_results.append(
                ResultPanelComponent(tool_name=f"tool-{i}", output=f"out-{i}", exit_code=0, is_recent=True)
            )
        renderer.state.selected_index = 0

        errors: list[Exception] = []
        barrier = threading.Barrier(20)

        def send_broadcasts() -> None:
            try:
                barrier.wait(timeout=5)
                for i in range(10):
                    renderer.notify(
                        agent,
                        {
                            "trace_outputs": {
                                "tool_results": [{"function": f"new-{i}", "output": "", "exit_code": 0}],
                            },
                        },
                    )
            except Exception as e:
                errors.append(e)

        def do_navigation() -> None:
            try:
                barrier.wait(timeout=5)
                for _ in range(10):
                    renderer.select_down()
                    renderer.toggle_expand()
                    renderer.select_up()
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(10):
            threads.append(threading.Thread(target=send_broadcasts))
            threads.append(threading.Thread(target=do_navigation))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent broadcast+nav raised errors: {errors}"


class TestLockSerializesBroadcasts:
    """Verify that the lock actually serializes access."""

    def test_broadcasts_are_serialized(self) -> None:
        """Verify that concurrent notify calls don't interleave handler execution."""
        renderer = _make_renderer()
        agent = _FakeAgent()

        # Track entry/exit of handlers to detect interleaving
        execution_log: list[str] = []
        log_lock = threading.Lock()

        original_handle_see = renderer._handle_see

        def tracked_handle_see(notifier: object, data: dict) -> None:  # type: ignore[type-arg]
            with log_lock:
                execution_log.append("see_start")
            original_handle_see(notifier, data)
            with log_lock:
                execution_log.append("see_end")

        renderer._handle_see = tracked_handle_see  # type: ignore[method-assign]

        barrier = threading.Barrier(5)

        def send_see() -> None:
            barrier.wait(timeout=5)
            renderer.notify(agent, {"trace_percepts": {"perception": "test"}})

        threads = [threading.Thread(target=send_see) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # All see_start/see_end pairs should be properly interleaved (no nesting)
        # With lock: see_start, see_end, see_start, see_end, ...
        # Without lock: could be see_start, see_start, ... (interleaved)
        assert len(execution_log) == 10  # 5 starts + 5 ends
        for i in range(0, len(execution_log), 2):
            assert execution_log[i] == "see_start"
            assert execution_log[i + 1] == "see_end"


class TestNoDataCorruptionUnderLoad:
    """Stress tests for data integrity under concurrent access."""

    def test_result_count_integrity(self) -> None:
        """Each ACT broadcast adds exactly one result - total should match thread count."""
        renderer = _make_renderer()
        agent = _FakeAgent()
        num_threads = 50
        barrier = threading.Barrier(num_threads)
        errors: list[Exception] = []

        def send_act(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(
                    agent,
                    {
                        "trace_outputs": {
                            "tool_results": [{"function": f"tool-{i}", "output": f"result-{i}", "exit_code": 0}],
                        },
                    },
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=send_act, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert not errors, f"Stress test raised errors: {errors}"
        assert len(renderer.state.current_turn_results) == num_threads

    def test_todo_update_integrity(self) -> None:
        """Concurrent THINK broadcasts with todo_list should not corrupt todo_items."""
        renderer = _make_renderer()
        agent = _FakeAgent()
        num_threads = 20
        barrier = threading.Barrier(num_threads)
        errors: list[Exception] = []

        def send_think_with_todos(i: int) -> None:
            try:
                barrier.wait(timeout=5)
                renderer.notify(
                    agent,
                    {
                        "trace_thoughts": {
                            "response": f"chunk-{i}",
                            "todo_list": [{"task": f"task-{i}", "status": "pending"}],
                        },
                    },
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=send_think_with_todos, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Todo update stress test raised errors: {errors}"
        # todo_items should be a valid list (one of the updates won)
        assert isinstance(renderer.state.todo_items, list)
        assert len(renderer.state.todo_items) == 1  # Last write wins
