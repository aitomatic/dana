"""Tests for graceful degradation in limited terminals.

Verifies that RichCLIRenderer works correctly in terminals with:
- No color support (plain text fallback)
- Narrow width (<80 columns)
- Terminal resize events
"""

import io
import signal
from unittest.mock import MagicMock

from rich.console import Console

from dana.cli.rich_cli_renderer import _MIN_RICH_WIDTH, RichCLIRenderer


class _FakeAgent:
    """Minimal fake agent for testing notify()."""

    def __init__(self, object_id: str = "test-agent") -> None:
        self.object_id = object_id
        self.agent_type = "star"
        self._star_loop_count = 0
        self.max_turns = 10


def _make_no_color_renderer() -> RichCLIRenderer:
    """Create a renderer with no color support."""
    console = Console(color_system=None, file=io.StringIO(), width=120)
    renderer = RichCLIRenderer(console=console)
    return renderer


def _make_narrow_renderer(width: int = 40) -> RichCLIRenderer:
    """Create a renderer with a narrow terminal."""
    console = Console(file=io.StringIO(), width=width, force_terminal=True)
    renderer = RichCLIRenderer(console=console)
    renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
    renderer._stop_live = MagicMock()  # type: ignore[method-assign]
    renderer._refresh_display = MagicMock()  # type: ignore[method-assign]
    return renderer


def _make_color_renderer() -> RichCLIRenderer:
    """Create a renderer with color support for comparison."""
    console = Console(file=io.StringIO(), width=120, force_terminal=True)
    renderer = RichCLIRenderer(console=console)
    renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
    renderer._stop_live = MagicMock()  # type: ignore[method-assign]
    renderer._refresh_display = MagicMock()  # type: ignore[method-assign]
    return renderer


# --- Terminal Capability Detection ---


class TestCapabilityDetection:
    """Verify terminal capability detection."""

    def test_no_color_detected(self) -> None:
        console = Console(color_system=None, file=io.StringIO())
        renderer = RichCLIRenderer(console=console)
        assert renderer.has_color is False

    def test_color_detected(self) -> None:
        console = Console(force_terminal=True, file=io.StringIO())
        renderer = RichCLIRenderer(console=console)
        assert renderer.has_color is True

    def test_terminal_width_property(self) -> None:
        console = Console(width=60, file=io.StringIO())
        renderer = RichCLIRenderer(console=console)
        assert renderer.terminal_width == 60

    def test_is_narrow_below_threshold(self) -> None:
        console = Console(width=40, file=io.StringIO())
        renderer = RichCLIRenderer(console=console)
        assert renderer.is_narrow is True

    def test_is_narrow_at_threshold(self) -> None:
        console = Console(width=_MIN_RICH_WIDTH, file=io.StringIO())
        renderer = RichCLIRenderer(console=console)
        assert renderer.is_narrow is False

    def test_is_narrow_above_threshold(self) -> None:
        console = Console(width=120, file=io.StringIO())
        renderer = RichCLIRenderer(console=console)
        assert renderer.is_narrow is False

    def test_has_color_attribute_set(self) -> None:
        renderer = _make_no_color_renderer()
        assert hasattr(renderer, "_has_color")


# --- Plain Text Fallback (No Color) ---


class TestPlainTextFallback:
    """Verify plain text output when terminal has no color support."""

    def test_no_color_skips_live(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_percepts": {"perception": "hello"}})
        # Live should never start
        assert renderer._live is None

    def test_no_color_see_prints_text(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_percepts": {"perception": "input received"}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "[SEE]" in output
        assert "Processing" in output

    def test_no_color_think_prints_text(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_thoughts": {"response": "thinking...", "done": False}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "[THINK]" in output
        assert "Thinking" in output

    def test_no_color_think_done_prints_response(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_thoughts": {"response": "Final answer here", "done": True}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "Final answer here" in output

    def test_no_color_act_prints_text(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_outputs": {"tool_calls": [{"function": "bash"}]}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "[ACT]" in output

    def test_no_color_tool_cards_plain_text(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        # Queue a tool call then flush via act
        renderer.notify(
            agent,
            {
                "trace_thoughts": {
                    "tool_calls": [{"function": "bash", "arguments": {"command": "ls"}}],
                    "done": False,
                }
            },
        )
        renderer.notify(agent, {"trace_outputs": {"tool_calls": [{"function": "bash"}]}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "-> bash" in output
        assert "command=ls" in output

    def test_no_color_tool_cards_no_panel(self) -> None:
        """In no-color mode, tool cards should NOT use Panel rendering."""
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(
            agent,
            {
                "trace_thoughts": {
                    "tool_calls": [{"function": "read_file", "arguments": {"path": "/foo/bar"}}],
                    "done": False,
                }
            },
        )
        renderer.notify(agent, {"trace_outputs": {"tool_calls": []}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        # Should be plain text, not rich panel
        assert "-> read_file" in output
        assert "path=/foo/bar" in output


class TestPlainTextDoneResponse:
    """Verify done response handling in no-color mode."""

    def test_done_response_plain_string(self) -> None:
        """In no-color mode, done response should be printed as plain string."""
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_thoughts": {"response": "Hello world", "done": True}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "Hello world" in output


# --- Narrow Terminal Handling ---


class TestNarrowTerminal:
    """Verify content truncation for narrow terminals."""

    def test_truncate_for_width_basic(self) -> None:
        renderer = _make_narrow_renderer(width=40)
        result = renderer._truncate_for_width("a" * 100)
        # Should be truncated to (40-6-1) + ellipsis = 34 chars
        assert len(result) <= 40
        assert result.endswith("…")

    def test_truncate_for_width_short_text(self) -> None:
        renderer = _make_narrow_renderer(width=40)
        result = renderer._truncate_for_width("short text")
        assert result == "short text"

    def test_truncate_for_width_custom_max(self) -> None:
        renderer = _make_narrow_renderer(width=40)
        result = renderer._truncate_for_width("hello world", max_width=5)
        assert result == "hell…"
        assert len(result) == 5

    def test_truncate_for_width_exact_fit(self) -> None:
        renderer = _make_narrow_renderer(width=40)
        result = renderer._truncate_for_width("abc", max_width=3)
        assert result == "abc"

    def test_narrow_tool_card_truncates_params(self) -> None:
        """In narrow + no-color mode, tool card params should be truncated."""
        console = Console(color_system=None, file=io.StringIO(), width=40)
        renderer = RichCLIRenderer(console=console)
        agent = _FakeAgent()
        long_command = "very-long-command " + "a" * 200
        renderer.notify(
            agent,
            {
                "trace_thoughts": {
                    "tool_calls": [{"function": "bash", "arguments": {"command": long_command}}],
                    "done": False,
                }
            },
        )
        renderer.notify(agent, {"trace_outputs": {"tool_calls": []}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        # Output should contain the tool name but params should be truncated
        assert "-> bash" in output
        assert "…" in output

    def test_very_narrow_terminal_minimum(self) -> None:
        """Even very narrow terminals should not crash."""
        console = Console(color_system=None, file=io.StringIO(), width=10)
        renderer = RichCLIRenderer(console=console)
        result = renderer._truncate_for_width("this is a long string")
        # Should truncate but not crash - min width is 10
        assert len(result) <= 10


# --- Terminal Resize Handling ---


class TestResizeHandling:
    """Verify terminal resize events are handled gracefully."""

    def test_resize_handler_installed(self) -> None:
        """SIGWINCH handler should be installed on supported platforms."""
        if not hasattr(signal, "SIGWINCH"):
            return  # Skip on Windows
        RichCLIRenderer(console=Console(file=io.StringIO()))
        # Handler should be installed (even if it's our wrapper)
        current_handler = signal.getsignal(signal.SIGWINCH)
        assert current_handler is not None
        assert current_handler != signal.SIG_DFL
        # Verify handler is callable (our wrapper)
        assert callable(current_handler)

    def test_resize_does_not_crash(self) -> None:
        """Sending SIGWINCH should not crash the renderer."""
        if not hasattr(signal, "SIGWINCH"):
            return  # Skip on Windows
        console = Console(file=io.StringIO(), force_terminal=True)
        renderer = RichCLIRenderer(console=console)
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        # Simulate resize by calling the handler directly
        handler = signal.getsignal(signal.SIGWINCH)
        if callable(handler):
            handler(signal.SIGWINCH, None)
        # Should not crash
        assert True

    def test_resize_calls_refresh(self) -> None:
        """Resize should trigger a display refresh."""
        if not hasattr(signal, "SIGWINCH"):
            return  # Skip on Windows
        console = Console(file=io.StringIO(), force_terminal=True)
        renderer = RichCLIRenderer(console=console)
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]
        handler = signal.getsignal(signal.SIGWINCH)
        if callable(handler):
            handler(signal.SIGWINCH, None)
            renderer._refresh_display.assert_called()  # type: ignore[attr-defined]

    def test_resize_handler_chains_previous(self) -> None:
        """Resize handler should chain to previous handler."""
        if not hasattr(signal, "SIGWINCH"):
            return  # Skip on Windows
        call_count = [0]

        def prev_handler(signum: int, frame: object) -> None:
            call_count[0] += 1

        signal.signal(signal.SIGWINCH, prev_handler)
        console = Console(file=io.StringIO())
        RichCLIRenderer(console=console)
        handler = signal.getsignal(signal.SIGWINCH)
        if callable(handler):
            handler(signal.SIGWINCH, None)
            assert call_count[0] == 1

    def test_resize_handler_non_main_thread(self) -> None:
        """Resize handler installation should not crash from non-main thread."""
        import threading

        errors: list[Exception] = []

        def create_renderer() -> None:
            try:
                console = Console(file=io.StringIO())
                RichCLIRenderer(console=console)
            except Exception as e:
                errors.append(e)

        t = threading.Thread(target=create_renderer)
        t.start()
        t.join()
        # Should not crash - just silently skip handler installation
        assert len(errors) == 0


# --- Color vs No-Color Comparison ---


class TestColorComparison:
    """Verify behavior differences between color and no-color modes."""

    def test_color_mode_uses_live(self) -> None:
        renderer = _make_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_percepts": {"perception": "hello"}})
        renderer._ensure_live.assert_called()  # type: ignore[attr-defined]

    def test_no_color_mode_skips_live(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_percepts": {"perception": "hello"}})
        assert renderer._live is None

    def test_color_mode_has_color_true(self) -> None:
        renderer = _make_color_renderer()
        assert renderer.has_color is True

    def test_no_color_mode_has_color_false(self) -> None:
        renderer = _make_no_color_renderer()
        assert renderer.has_color is False


# --- Edge Cases ---


class TestEdgeCases:
    """Edge cases for degraded rendering."""

    def test_empty_tool_card_no_crash(self) -> None:
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(
            agent,
            {
                "trace_thoughts": {
                    "tool_calls": [{"function": "bash", "arguments": {}}],
                    "done": False,
                }
            },
        )
        renderer.notify(agent, {"trace_outputs": {"tool_calls": []}})
        output = renderer.console.file.getvalue()  # type: ignore[union-attr]
        assert "-> bash" in output

    def test_truncate_empty_string(self) -> None:
        renderer = _make_narrow_renderer()
        assert renderer._truncate_for_width("") == ""

    def test_truncate_single_char(self) -> None:
        renderer = _make_narrow_renderer()
        assert renderer._truncate_for_width("x") == "x"

    def test_no_color_with_progress_tracker(self) -> None:
        """Progress tracker should work in no-color mode."""
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(
            agent,
            {
                "trace_thoughts": {
                    "todo_list": [{"content": "Task 1", "status": "in_progress"}],
                    "done": False,
                }
            },
        )
        assert renderer.state.todo_items == [{"content": "Task 1", "status": "in_progress"}]

    def test_no_color_with_status_line(self) -> None:
        """Status line should still track state in no-color mode."""
        renderer = _make_no_color_renderer()
        agent = _FakeAgent(object_id="my-agent")
        renderer.notify(agent, {"trace_percepts": {"perception": "hello"}})
        assert renderer.state.current_agent_id == "my-agent"

    def test_no_color_result_panels_still_stored(self) -> None:
        """Result panels should still be stored in state even in no-color mode."""
        renderer = _make_no_color_renderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"trace_outputs": {"tool_results": [{"function": "bash", "output": "hello", "exit_code": 0}]}})
        assert len(renderer.state.current_turn_results) == 1
