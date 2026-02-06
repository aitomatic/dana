"""Tests for RichCLIRenderer message routing and spinner integration."""

from unittest.mock import MagicMock, patch

from rich.console import Console

from dana.cli.components.spinner import SpinnerComponent
from dana.cli.rich_cli_renderer import RichCLIRenderer


class _FakeAgent:
    """Minimal fake agent for testing notify()."""

    def __init__(self, object_id: str = "test-agent") -> None:
        self.object_id = object_id
        self.agent_type = "star"


class TestRichCLIRendererInit:
    """Test constructor and defaults."""

    def test_default_console(self) -> None:
        renderer = RichCLIRenderer()
        assert isinstance(renderer.console, Console)

    def test_custom_console(self) -> None:
        console = Console()
        renderer = RichCLIRenderer(console=console)
        assert renderer.console is console

    def test_default_options(self) -> None:
        renderer = RichCLIRenderer()
        assert renderer.verbose is True
        assert renderer.show_tool_calls is True
        assert renderer.show_reasoning is True
        assert renderer.max_output_lines == 50

    def test_custom_options(self) -> None:
        renderer = RichCLIRenderer(
            verbose=False,
            show_tool_calls=False,
            show_reasoning=False,
            max_output_lines=20,
        )
        assert renderer.verbose is False
        assert renderer.show_tool_calls is False
        assert renderer.show_reasoning is False
        assert renderer.max_output_lines == 20

    def test_has_render_state(self) -> None:
        from dana.cli.state import RenderState

        renderer = RichCLIRenderer()
        assert isinstance(renderer.state, RenderState)

    def test_has_spinner_component(self) -> None:
        renderer = RichCLIRenderer()
        assert isinstance(renderer._spinner, SpinnerComponent)

    def test_live_initially_none(self) -> None:
        renderer = RichCLIRenderer()
        assert renderer._live is None


class TestNotifyRouting:
    """Test that notify() routes messages to the correct handler."""

    def test_trace_percepts_routes_to_handle_see(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        data = {"caller_message": "hello"}

        with patch.object(renderer, "_handle_see") as mock:
            renderer.notify(agent, {"trace_percepts": data})
            mock.assert_called_once_with(agent, data)

    def test_trace_thoughts_routes_to_handle_think(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        data = {"response": "thinking..."}

        with patch.object(renderer, "_handle_think") as mock:
            renderer.notify(agent, {"trace_thoughts": data})
            mock.assert_called_once_with(agent, data)

    def test_trace_outputs_routes_to_handle_act(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        data = {"tool_calls": [{"function": "bash"}]}

        with patch.object(renderer, "_handle_act") as mock:
            renderer.notify(agent, {"trace_outputs": data})
            mock.assert_called_once_with(agent, data)

    def test_trace_learning_routes_to_handle_reflect(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        data = {"learning_note": "learned something"}

        with patch.object(renderer, "_handle_reflect") as mock:
            renderer.notify(agent, {"trace_learning": data})
            mock.assert_called_once_with(agent, data)

    def test_workflow_progress_routes_to_handle_workflow(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        data = {"workflow_id": "wf-1", "phase": "start"}

        with patch.object(renderer, "_handle_workflow") as mock:
            renderer.notify(agent, {"workflow_progress": data})
            mock.assert_called_once_with(agent, data)

    def test_skill_progress_routes_to_handle_skill(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        data = {"skill_id": "claude-skills", "phase": "execute"}

        with patch.object(renderer, "_handle_skill") as mock:
            renderer.notify(agent, {"skill_progress": data})
            mock.assert_called_once_with(agent, data)

    def test_unknown_key_ignored(self) -> None:
        """Messages with unrecognized keys should not raise."""
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        renderer.notify(agent, {"unknown_key": {"data": 1}})

    def test_empty_message_ignored(self) -> None:
        """Empty messages should not raise."""
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        renderer.notify(agent, {})

    def test_multiple_keys_route_to_multiple_handlers(self) -> None:
        """A message with multiple broadcast keys calls all matching handlers."""
        renderer = RichCLIRenderer()
        agent = _FakeAgent()
        percepts_data = {"caller_message": "hello"}
        thoughts_data = {"response": "thinking"}

        with (
            patch.object(renderer, "_handle_see") as mock_see,
            patch.object(renderer, "_handle_think") as mock_think,
        ):
            renderer.notify(
                agent,
                {"trace_percepts": percepts_data, "trace_thoughts": thoughts_data},
            )
            mock_see.assert_called_once_with(agent, percepts_data)
            mock_think.assert_called_once_with(agent, thoughts_data)


class TestAgentContext:
    """Test that notify() updates agent context in RenderState."""

    def test_updates_agent_id(self) -> None:
        renderer = RichCLIRenderer()
        agent = _FakeAgent(object_id="my-agent")
        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer.state.current_agent_id == "my-agent"

    def test_unknown_agent_id(self) -> None:
        renderer = RichCLIRenderer()
        renderer.notify(object(), {})
        assert renderer.state.current_agent_id == "unknown"


class TestNotifiableProtocol:
    """Test that RichCLIRenderer satisfies the Notifiable protocol."""

    def test_is_notifiable_instance(self) -> None:
        from dana.common.protocols import Notifiable

        renderer = RichCLIRenderer()
        assert isinstance(renderer, Notifiable)

    def test_import_from_package(self) -> None:
        from dana.cli import RichCLIRenderer as ImportedRenderer

        assert ImportedRenderer is RichCLIRenderer


class TestSpinnerIntegration:
    """Test spinner phase updates through handler methods."""

    def _make_renderer(self) -> RichCLIRenderer:
        """Create a renderer with Live mocked to avoid terminal output."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> MagicMock:
        """Replace _ensure_live and _stop_live with no-ops, _refresh_display too."""
        mock_live = MagicMock()
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]
        return mock_live

    def test_handle_see_starts_spinner(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        assert renderer._spinner.running is False
        renderer._handle_see(agent, {"caller_message": "hello"})
        assert renderer._spinner.running is True

    def test_handle_see_updates_phase(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_see(agent, {"perception": "Perceived 3 tool result(s)"})
        assert renderer.state.current_phase == "SEE"
        assert renderer._spinner.text == "Processing..."

    def test_handle_see_with_perception_context(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_see(agent, {"perception": "Perceived 2 tool result(s)"})
        # SpinnerComponent ignores unknown context keys for SEE phase
        assert renderer._spinner.text == "Processing..."

    def test_handle_think_updates_phase(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "tool_calls": []})
        assert renderer.state.current_phase == "THINK"
        assert renderer._spinner.text == "Thinking..."

    def test_handle_think_starts_spinner(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False})
        assert renderer._spinner.running is True

    def test_handle_think_extracts_tool_calls(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [
            {"function": "bash", "arguments": {"command": "ls"}},
            {"function": "read_file", "arguments": {"path": "/tmp/test"}},
        ]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})
        assert renderer.state.current_phase == "THINK"
        # SpinnerComponent receives tool_calls in context but THINK phase
        # still shows "Thinking..." (tool_calls context is for future use)
        assert renderer._spinner.text == "Thinking..."

    def test_handle_think_done_stops_spinner(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Start spinner first
        renderer._handle_see(agent, {"caller_message": "hello"})
        assert renderer._spinner.running is True

        # Done=True should stop spinner
        renderer._handle_think(agent, {"done": True, "response": "Here is the answer"})
        assert renderer._spinner.running is False

    def test_handle_think_done_stops_live(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": True, "response": "answer"})
        renderer._stop_live.assert_called_once()  # type: ignore[attr-defined]

    def test_handle_think_done_prints_response_when_verbose(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()
        renderer.verbose = True

        with patch.object(renderer.console, "print") as mock_print:
            renderer._handle_think(agent, {"done": True, "response": "Final answer"})
            mock_print.assert_called_once()

    def test_handle_think_done_no_print_when_not_verbose(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()
        renderer.verbose = False

        with patch.object(renderer.console, "print") as mock_print:
            renderer._handle_think(agent, {"done": True, "response": "Final answer"})
            mock_print.assert_not_called()

    def test_handle_think_done_no_print_empty_response(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()
        renderer.verbose = True

        with patch.object(renderer.console, "print") as mock_print:
            renderer._handle_think(agent, {"done": True, "response": ""})
            mock_print.assert_not_called()

    def test_handle_act_updates_phase(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [{"function": "bash", "arguments": {"command": "ls"}}]
        renderer._handle_act(agent, {"tool_calls": tool_calls})
        assert renderer.state.current_phase == "ACT"
        assert renderer._spinner.text == "Executing bash..."

    def test_handle_act_starts_spinner(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_act(agent, {"tool_calls": []})
        assert renderer._spinner.running is True

    def test_handle_act_multiple_tools(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [
            {"function": "bash", "arguments": {}},
            {"function": "grep", "arguments": {}},
        ]
        renderer._handle_act(agent, {"tool_calls": tool_calls})
        assert renderer._spinner.text == "Executing bash, grep..."

    def test_handle_act_no_tool_calls(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_act(agent, {})
        assert renderer._spinner.text == "Executing..."

    def test_full_star_loop_phase_transitions(self) -> None:
        """Verify spinner phases through a complete STAR loop."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # SEE phase
        renderer._handle_see(agent, {"caller_message": "hello", "perception": ""})
        assert renderer.state.current_phase == "SEE"
        assert renderer._spinner.running is True
        assert renderer._spinner.text == "Processing..."

        # THINK phase (not done, has tool_calls)
        renderer._handle_think(
            agent,
            {
                "done": False,
                "tool_calls": [{"function": "bash", "arguments": {"command": "ls"}}],
                "reasoning": "I need to list files",
            },
        )
        assert renderer.state.current_phase == "THINK"
        assert renderer._spinner.running is True
        assert renderer._spinner.text == "Thinking..."

        # ACT phase
        renderer._handle_act(
            agent,
            {
                "tool_calls": [{"function": "bash", "arguments": {"command": "ls"}}],
                "tool_results": [{"output": "file1.py\nfile2.py"}],
            },
        )
        assert renderer.state.current_phase == "ACT"
        assert renderer._spinner.running is True
        assert renderer._spinner.text == "Executing bash..."

        # THINK phase (done)
        renderer._handle_think(
            agent,
            {"done": True, "response": "Found 2 files", "tool_calls": []},
        )
        assert renderer.state.current_phase == "THINK"
        assert renderer._spinner.running is False

    def test_spinner_survives_multiple_star_loops(self) -> None:
        """Verify spinner restarts on new SEE phase after completion."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # First loop
        renderer._handle_see(agent, {"caller_message": "first"})
        assert renderer._spinner.running is True
        renderer._handle_think(agent, {"done": True, "response": "done"})
        assert renderer._spinner.running is False

        # Second loop - spinner should restart
        renderer._handle_see(agent, {"caller_message": "second"})
        assert renderer._spinner.running is True

    def test_handle_see_calls_refresh(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_see(agent, {"caller_message": "hi"})
        renderer._refresh_display.assert_called()  # type: ignore[attr-defined]

    def test_handle_think_calls_refresh_when_not_done(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False})
        renderer._refresh_display.assert_called()  # type: ignore[attr-defined]

    def test_handle_act_calls_refresh(self) -> None:
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_act(agent, {"tool_calls": []})
        renderer._refresh_display.assert_called()  # type: ignore[attr-defined]


class TestLiveContextManagement:
    """Test _ensure_live, _stop_live, and _refresh_display methods."""

    def test_ensure_live_creates_live_instance(self) -> None:
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        assert renderer._live is None
        renderer._ensure_live()
        assert renderer._live is not None
        # Clean up
        renderer._stop_live()

    def test_ensure_live_idempotent(self) -> None:
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        renderer._ensure_live()
        first_live = renderer._live
        renderer._ensure_live()
        assert renderer._live is first_live
        # Clean up
        renderer._stop_live()

    def test_stop_live_clears_instance(self) -> None:
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        renderer._ensure_live()
        assert renderer._live is not None
        renderer._stop_live()
        assert renderer._live is None

    def test_stop_live_noop_when_no_live(self) -> None:
        renderer = RichCLIRenderer()
        renderer._stop_live()  # Should not raise
        assert renderer._live is None

    def test_refresh_display_noop_when_no_live(self) -> None:
        renderer = RichCLIRenderer()
        renderer._refresh_display()  # Should not raise
