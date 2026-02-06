"""Tests for RichCLIRenderer message routing, spinner, streaming, status line, and result panel integration."""

from unittest.mock import MagicMock, patch

from rich.console import Console
from rich.panel import Panel

from dana.cli.components.progress_tracker import ProgressTrackerComponent
from dana.cli.components.result_panel import ResultPanelComponent
from dana.cli.components.spinner import SpinnerComponent
from dana.cli.components.status_line import StatusLineComponent
from dana.cli.components.stream_display import StreamDisplayComponent
from dana.cli.components.tool_card import ToolCardComponent
from dana.cli.rich_cli_renderer import RichCLIRenderer


class _FakeAgent:
    """Minimal fake agent for testing notify()."""

    def __init__(
        self,
        object_id: str = "test-agent",
        model: str = "",
        star_loop_count: int = 0,
        max_turns: int = 0,
    ) -> None:
        self.object_id = object_id
        self.agent_type = "star"
        if model:
            self.llm_client = type("LLMClient", (), {"model": model})()
        self._star_loop_count = star_loop_count
        self.max_turns = max_turns


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

    def test_has_stream_display_component(self) -> None:
        renderer = RichCLIRenderer()
        assert isinstance(renderer._stream_display, StreamDisplayComponent)

    def test_stream_display_uses_max_output_lines(self) -> None:
        renderer = RichCLIRenderer(max_output_lines=30)
        assert renderer._stream_display._line_threshold == 30

    def test_has_tool_card_component(self) -> None:
        renderer = RichCLIRenderer()
        assert isinstance(renderer._tool_card, ToolCardComponent)

    def test_pending_tool_cards_initially_empty(self) -> None:
        renderer = RichCLIRenderer()
        assert renderer._pending_tool_cards == []

    def test_has_status_line_component(self) -> None:
        renderer = RichCLIRenderer()
        assert isinstance(renderer._status_line, StatusLineComponent)

    def test_has_progress_tracker_component(self) -> None:
        renderer = RichCLIRenderer()
        assert isinstance(renderer._progress_tracker, ProgressTrackerComponent)

    def test_agent_stack_initially_empty(self) -> None:
        renderer = RichCLIRenderer()
        assert renderer._agent_stack == []

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


class TestToolCardIntegration:
    """Test tool card rendering through RichCLIRenderer handlers."""

    def _make_renderer(self) -> RichCLIRenderer:
        """Create a renderer with Live mocked to avoid terminal output."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        """Replace _ensure_live, _stop_live, _refresh_display with no-ops."""
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_handle_think_queues_tool_cards(self) -> None:
        """Tool calls in THINK phase are queued as pending tool cards."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [
            {"function": "bash", "arguments": {"command": "ls"}},
            {"function": "read_file", "arguments": {"path": "/tmp/test.py"}},
        ]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})
        assert len(renderer._pending_tool_cards) == 2
        assert renderer._pending_tool_cards[0]["function"] == "bash"
        assert renderer._pending_tool_cards[1]["function"] == "read_file"

    def test_handle_think_no_tool_cards_when_show_tool_calls_false(self) -> None:
        """Tool cards not queued when show_tool_calls is False."""
        renderer = self._make_renderer()
        renderer.show_tool_calls = False
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [{"function": "bash", "arguments": {"command": "ls"}}]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})
        assert len(renderer._pending_tool_cards) == 0

    def test_handle_think_no_tool_cards_when_empty_list(self) -> None:
        """No tool cards queued when tool_calls is empty."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "tool_calls": []})
        assert len(renderer._pending_tool_cards) == 0

    def test_handle_think_no_tool_cards_when_missing(self) -> None:
        """No tool cards queued when tool_calls is missing."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False})
        assert len(renderer._pending_tool_cards) == 0

    def test_handle_act_flushes_tool_cards(self) -> None:
        """ACT phase flushes pending tool cards via console.print."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Queue some tool cards via THINK
        tool_calls = [{"function": "bash", "arguments": {"command": "ls"}}]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})
        assert len(renderer._pending_tool_cards) == 1

        # ACT should flush them
        with patch.object(renderer.console, "print") as mock_print:
            renderer._handle_act(agent, {"tool_calls": tool_calls})
            assert mock_print.call_count == 1
            # Verify a Panel was printed
            printed_arg = mock_print.call_args[0][0]
            assert isinstance(printed_arg, Panel)

        # Queue should be empty after flush
        assert len(renderer._pending_tool_cards) == 0

    def test_handle_act_no_flush_when_no_pending(self) -> None:
        """ACT phase does not call console.print when no tool cards pending."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        with patch.object(renderer.console, "print") as mock_print:
            renderer._handle_act(agent, {"tool_calls": []})
            mock_print.assert_not_called()

    def test_tool_cards_chronological_order(self) -> None:
        """Tool cards are flushed in the order they were queued."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [
            {"function": "bash", "arguments": {"command": "ls"}},
            {"function": "grep", "arguments": {"pattern": "foo"}},
            {"function": "read_file", "arguments": {"path": "/test"}},
        ]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})

        printed_panels: list[Panel] = []
        with patch.object(renderer.console, "print", side_effect=lambda p: printed_panels.append(p)):
            renderer._handle_act(agent, {"tool_calls": tool_calls})

        assert len(printed_panels) == 3
        assert "bash" in str(printed_panels[0].title)
        assert "grep" in str(printed_panels[1].title)
        assert "read_file" in str(printed_panels[2].title)

    def test_tool_cards_render_before_spinner_in_act(self) -> None:
        """Tool cards are flushed before spinner update in ACT phase."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Queue tool cards
        tool_calls = [{"function": "bash", "arguments": {"command": "ls"}}]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})

        # Track call order
        call_order: list[str] = []

        original_flush = renderer._flush_tool_cards
        original_update = renderer._spinner.update_phase

        def mock_flush() -> None:
            call_order.append("flush")
            original_flush()

        def mock_update(phase: str, context: dict[str, object] | None = None) -> None:
            call_order.append("spinner_update")
            original_update(phase, context)

        renderer._flush_tool_cards = mock_flush  # type: ignore[method-assign]
        renderer._spinner.update_phase = mock_update  # type: ignore[method-assign]

        with patch.object(renderer.console, "print"):
            renderer._handle_act(agent, {"tool_calls": tool_calls})

        assert call_order.index("flush") < call_order.index("spinner_update")

    def test_handle_think_done_flushes_remaining_cards(self) -> None:
        """When done=True, any remaining tool cards are flushed."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Queue tool cards
        tool_calls = [{"function": "bash", "arguments": {"command": "ls"}}]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})
        assert len(renderer._pending_tool_cards) == 1

        # Done should flush remaining
        with patch.object(renderer.console, "print") as mock_print:
            renderer._handle_think(agent, {"done": True, "response": "done"})
            # One call for tool card, one for the response text
            assert mock_print.call_count == 2

        assert len(renderer._pending_tool_cards) == 0

    def test_flush_tool_cards_empty_is_noop(self) -> None:
        """_flush_tool_cards does nothing when queue is empty."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        with patch.object(renderer.console, "print") as mock_print:
            renderer._flush_tool_cards()
            mock_print.assert_not_called()

    def test_multiple_think_broadcasts_accumulate_cards(self) -> None:
        """Multiple THINK broadcasts accumulate tool cards."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(
            agent,
            {"done": False, "tool_calls": [{"function": "bash", "arguments": {}}]},
        )
        renderer._handle_think(
            agent,
            {"done": False, "tool_calls": [{"function": "grep", "arguments": {}}]},
        )

        assert len(renderer._pending_tool_cards) == 2
        assert renderer._pending_tool_cards[0]["function"] == "bash"
        assert renderer._pending_tool_cards[1]["function"] == "grep"

    def test_tool_card_content_correct(self) -> None:
        """Flushed tool cards contain correct tool information."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [
            {"function": "bash", "arguments": {"command": "echo hello"}},
        ]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})

        printed_panels: list[Panel] = []
        with patch.object(renderer.console, "print", side_effect=lambda p: printed_panels.append(p)):
            renderer._flush_tool_cards()

        assert len(printed_panels) == 1
        panel = printed_panels[0]
        assert "bash" in str(panel.title)
        body_text = str(panel.renderable)
        assert "echo hello" in body_text

    def test_skips_non_dict_tool_calls(self) -> None:
        """Non-dict items in tool_calls are skipped."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_calls = [
            {"function": "bash", "arguments": {}},
            "not a dict",
            42,
            {"function": "grep", "arguments": {}},
        ]
        renderer._handle_think(agent, {"done": False, "tool_calls": tool_calls})
        assert len(renderer._pending_tool_cards) == 2


class TestStreamDisplayIntegration:
    """Test streaming text display through RichCLIRenderer handlers."""

    def _make_renderer(self) -> RichCLIRenderer:
        """Create a renderer with Live mocked to avoid terminal output."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        """Replace _ensure_live, _stop_live, _refresh_display with no-ops."""
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_handle_think_streams_response_text(self) -> None:
        """Response text in THINK broadcasts is appended to stream display."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "response": "Hello "})
        assert renderer._stream_display.buffer == "Hello "

    def test_handle_think_accumulates_chunks(self) -> None:
        """Multiple THINK broadcasts accumulate text in stream display."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "response": "Hello "})
        renderer._handle_think(agent, {"done": False, "response": "world!"})
        assert renderer._stream_display.buffer == "Hello world!"

    def test_handle_think_no_stream_when_empty_response(self) -> None:
        """Empty response does not add to stream display."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "response": ""})
        assert renderer._stream_display.buffer == ""

    def test_handle_think_no_stream_when_no_response(self) -> None:
        """Missing response key does not add to stream display."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False})
        assert renderer._stream_display.buffer == ""

    def test_handle_see_clears_stream_display(self) -> None:
        """SEE phase clears the stream display for a new STAR loop."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Accumulate some text
        renderer._handle_think(agent, {"done": False, "response": "first response"})
        assert renderer._stream_display.buffer == "first response"

        # New STAR loop via SEE should clear
        renderer._handle_see(agent, {"caller_message": "new question"})
        assert renderer._stream_display.buffer == ""

    def test_stream_display_clears_between_star_loops(self) -> None:
        """Stream display resets between consecutive STAR loops."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # First loop
        renderer._handle_see(agent, {"caller_message": "first"})
        renderer._handle_think(agent, {"done": False, "response": "answer 1"})
        assert renderer._stream_display.buffer == "answer 1"

        renderer._handle_think(agent, {"done": True, "response": "final 1"})

        # Second loop - SEE should clear stream
        renderer._handle_see(agent, {"caller_message": "second"})
        assert renderer._stream_display.buffer == ""

        renderer._handle_think(agent, {"done": False, "response": "answer 2"})
        assert renderer._stream_display.buffer == "answer 2"

    def test_handle_think_done_does_not_stream(self) -> None:
        """When done=True, response is printed (not streamed)."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": True, "response": "Final answer"})
        # Stream should be empty - done response is printed, not streamed
        assert renderer._stream_display.buffer == ""

    def test_stream_display_calls_refresh(self) -> None:
        """Streaming text triggers a display refresh."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "response": "chunk"})
        renderer._refresh_display.assert_called()  # type: ignore[attr-defined]

    def test_refresh_display_includes_stream_text(self) -> None:
        """_refresh_display includes stream display content in Live update."""
        renderer = self._make_renderer()

        # Use real _refresh_display but mock Live
        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()

        # Add some streamed text
        renderer._stream_display.append_chunk("Streaming text here")
        renderer._refresh_display()

        # Live.update should have been called with a Group containing both
        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        # Group should contain spinner text + stream text
        assert hasattr(group, "renderables")
        assert len(group.renderables) == 2

    def test_refresh_display_shows_stream_only_when_spinner_stopped(self) -> None:
        """Stream text shows even if spinner is not running."""
        renderer = self._make_renderer()

        mock_live = MagicMock()
        renderer._live = mock_live
        # Spinner not running, but stream has content
        renderer._stream_display.append_chunk("Some text")
        renderer._refresh_display()

        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        assert len(group.renderables) == 1  # Only stream text

    def test_refresh_display_empty_when_no_content(self) -> None:
        """Refresh shows empty text when neither spinner nor stream has content."""
        renderer = self._make_renderer()

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._refresh_display()

        mock_live.update.assert_called_once()
        # Should be an empty Text
        arg = mock_live.update.call_args[0][0]
        from rich.text import Text

        assert isinstance(arg, Text)
        assert str(arg) == ""

    def test_stream_and_tool_calls_coexist(self) -> None:
        """Streaming text and tool calls work together in THINK phase."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # THINK with both response and tool_calls
        renderer._handle_think(
            agent,
            {
                "done": False,
                "response": "I'll check that for you",
                "tool_calls": [{"function": "bash", "arguments": {"command": "ls"}}],
            },
        )
        assert renderer._stream_display.buffer == "I'll check that for you"
        assert len(renderer._pending_tool_cards) == 1


class TestStatusLineIntegration:
    """Test status line updates through RichCLIRenderer handlers."""

    def _make_renderer(self) -> RichCLIRenderer:
        """Create a renderer with Live mocked to avoid terminal output."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        """Replace _ensure_live, _stop_live, _refresh_display with no-ops."""
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_status_line_updates_on_notify(self) -> None:
        """Status line updates with agent context on each broadcast."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent(object_id="my-agent", model="gpt-4", star_loop_count=2, max_turns=5)

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hello"}})

        assert renderer._status_line.agent_id == "my-agent"
        assert renderer._status_line.model == "gpt-4"
        assert renderer._status_line.turn == 2
        assert renderer._status_line.max_turns == 5

    def test_status_line_render_format(self) -> None:
        """Status line renders with correct format from agent context."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent(object_id="agent-1", model="claude-3", star_loop_count=1, max_turns=3)

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})

        status = renderer._status_line.render()
        assert "agent-1" in status
        assert "claude-3" in status
        assert "turn 1/3" in status

    def test_status_line_no_turn_when_zero(self) -> None:
        """Turn info hidden when turn is 0."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent(object_id="agent-1", model="claude-3", star_loop_count=0, max_turns=5)

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})

        status = renderer._status_line.render()
        assert "agent-1" in status
        assert "turn" not in status

    def test_status_line_updates_on_each_broadcast(self) -> None:
        """Status line updates with each notify call."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        agent1 = _FakeAgent(object_id="agent-1", model="gpt-4", star_loop_count=1, max_turns=3)
        renderer.notify(agent1, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer._status_line.agent_id == "agent-1"

        agent2 = _FakeAgent(object_id="agent-1", model="gpt-4", star_loop_count=2, max_turns=3)
        renderer.notify(agent2, {"trace_thoughts": {"done": False}})
        assert renderer._status_line.turn == 2

    def test_state_updates_model_from_llm_client(self) -> None:
        """Model is extracted from notifier's llm_client attribute."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent(object_id="test", model="gpt-4-turbo")

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer.state.current_model == "gpt-4-turbo"

    def test_state_updates_model_from_llm_config_fallback(self) -> None:
        """Model falls back to _llm_config dict when no llm_client."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent(object_id="test")  # No model = no llm_client
        agent._llm_config = {"model": "claude-3-haiku"}  # type: ignore[attr-defined]

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer.state.current_model == "claude-3-haiku"

    def test_state_updates_turn_info(self) -> None:
        """Turn and max_turns are extracted from notifier."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent(object_id="test", star_loop_count=3, max_turns=10)

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer.state.current_turn == 3
        assert renderer.state.max_turns == 10


class TestSubagentTransitions:
    """Test status line behavior during agent transitions."""

    def _make_renderer(self) -> RichCLIRenderer:
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_subagent_invocation_pushes_parent(self) -> None:
        """When a new agent_id appears, parent is pushed onto stack."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        parent = _FakeAgent(object_id="parent-agent")
        child = _FakeAgent(object_id="child-agent")

        renderer.notify(parent, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer.state.current_agent_id == "parent-agent"
        assert renderer._agent_stack == []

        renderer.notify(child, {"trace_thoughts": {"done": False}})
        assert renderer.state.current_agent_id == "child-agent"
        assert renderer._agent_stack == ["parent-agent"]

    def test_subagent_completion_pops_stack(self) -> None:
        """When parent agent_id reappears, stack pops back to it."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        parent = _FakeAgent(object_id="parent-agent")
        child = _FakeAgent(object_id="child-agent")

        # Parent → Child
        renderer.notify(parent, {"trace_percepts": {"caller_message": "hi"}})
        renderer.notify(child, {"trace_thoughts": {"done": False}})
        assert renderer._agent_stack == ["parent-agent"]

        # Child → Parent (subagent completes)
        renderer.notify(parent, {"trace_thoughts": {"done": False}})
        assert renderer.state.current_agent_id == "parent-agent"
        assert renderer._agent_stack == []

    def test_status_updates_to_subagent(self) -> None:
        """Status line shows subagent info during subagent execution."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        parent = _FakeAgent(object_id="parent", model="gpt-4", star_loop_count=1, max_turns=5)
        child = _FakeAgent(object_id="child-task", model="gpt-3.5", star_loop_count=1, max_turns=3)

        renderer.notify(parent, {"trace_percepts": {"caller_message": "hi"}})
        assert renderer._status_line.agent_id == "parent"
        assert renderer._status_line.model == "gpt-4"

        renderer.notify(child, {"trace_thoughts": {"done": False}})
        assert renderer._status_line.agent_id == "child-task"
        assert renderer._status_line.model == "gpt-3.5"

    def test_status_returns_to_parent_after_subagent(self) -> None:
        """Status line returns to parent agent info when subagent completes."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        parent = _FakeAgent(object_id="parent", model="gpt-4", star_loop_count=2, max_turns=5)
        child = _FakeAgent(object_id="child", model="gpt-3.5", star_loop_count=1, max_turns=3)

        renderer.notify(parent, {"trace_percepts": {"caller_message": "hi"}})
        renderer.notify(child, {"trace_thoughts": {"done": False}})
        assert renderer._status_line.agent_id == "child"

        renderer.notify(parent, {"trace_thoughts": {"done": False}})
        assert renderer._status_line.agent_id == "parent"
        assert renderer._status_line.model == "gpt-4"

    def test_nested_subagents(self) -> None:
        """Handles nested subagent transitions (parent → child → grandchild → parent)."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        parent = _FakeAgent(object_id="parent")
        child = _FakeAgent(object_id="child")
        grandchild = _FakeAgent(object_id="grandchild")

        renderer.notify(parent, {"trace_percepts": {"caller_message": "hi"}})
        renderer.notify(child, {"trace_thoughts": {"done": False}})
        renderer.notify(grandchild, {"trace_thoughts": {"done": False}})
        assert renderer._agent_stack == ["parent", "child"]
        assert renderer.state.current_agent_id == "grandchild"

        # Grandchild completes → child
        renderer.notify(child, {"trace_thoughts": {"done": False}})
        assert renderer._agent_stack == ["parent"]
        assert renderer.state.current_agent_id == "child"

        # Child completes → parent
        renderer.notify(parent, {"trace_thoughts": {"done": False}})
        assert renderer._agent_stack == []
        assert renderer.state.current_agent_id == "parent"

    def test_same_agent_id_no_stack_change(self) -> None:
        """Consecutive broadcasts from the same agent don't modify the stack."""
        renderer = self._make_renderer()
        self._patch_live(renderer)

        agent = _FakeAgent(object_id="agent-1")

        renderer.notify(agent, {"trace_percepts": {"caller_message": "hi"}})
        renderer.notify(agent, {"trace_thoughts": {"done": False}})
        renderer.notify(agent, {"trace_outputs": {"tool_calls": []}})

        assert renderer._agent_stack == []
        assert renderer.state.current_agent_id == "agent-1"


class TestStatusLineInRefreshDisplay:
    """Test that status line appears in refresh display output."""

    def test_refresh_includes_status_line(self) -> None:
        """Status line text appears in Live display when agent context is set."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()

        # Set status line content
        renderer._status_line.update(agent_id="my-agent", model="gpt-4", turn=1, max_turns=3)
        renderer._refresh_display()

        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        # Spinner + status line = 2 renderables
        assert len(group.renderables) == 2

    def test_refresh_includes_status_with_stream(self) -> None:
        """Status line, spinner, and stream text all render together."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()
        renderer._stream_display.append_chunk("Some text")
        renderer._status_line.update(agent_id="agent", model="model")

        renderer._refresh_display()

        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        # Spinner + stream + status line = 3
        assert len(group.renderables) == 3

    def test_refresh_status_line_at_bottom(self) -> None:
        """Status line is the last renderable in the group (at bottom)."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()
        renderer._status_line.update(agent_id="agent-1", model="gpt-4", turn=1, max_turns=5)

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        last_renderable = group.renderables[-1]
        # Last renderable should contain status line text (dimmed)
        rendered_text = str(last_renderable)
        assert "agent-1" in rendered_text

    def test_refresh_no_status_when_empty(self) -> None:
        """No status line renderable when status line renders empty string."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()
        # Status line has no content set

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        # Only spinner, no status line
        assert len(group.renderables) == 1

    def test_status_only_when_spinner_stopped(self) -> None:
        """Status line shows even when spinner is not running."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._status_line.update(agent_id="agent", model="model")

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        assert len(group.renderables) == 1  # Only status line


class TestProgressTrackerIntegration:
    """Test progress tracker updates through RichCLIRenderer handlers."""

    def _make_renderer(self) -> RichCLIRenderer:
        """Create a renderer with Live mocked to avoid terminal output."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        """Replace _ensure_live, _stop_live, _refresh_display with no-ops."""
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_handle_think_updates_progress_tracker(self) -> None:
        """todo_list in THINK broadcasts updates the progress tracker."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        todos = [
            {"content": "Step 1", "status": "completed"},
            {"content": "Step 2", "status": "in_progress"},
            {"content": "Step 3", "status": "pending"},
        ]
        renderer._handle_think(agent, {"done": False, "todo_list": todos})

        assert renderer._progress_tracker.total_count == 3
        assert renderer._progress_tracker.completed_count == 1
        assert renderer._progress_tracker.current_task == "Step 2"

    def test_handle_think_updates_state_todo_items(self) -> None:
        """todo_list in THINK broadcasts updates RenderState.todo_items."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        todos = [
            {"content": "Task A", "status": "pending"},
            {"content": "Task B", "status": "in_progress"},
        ]
        renderer._handle_think(agent, {"done": False, "todo_list": todos})

        assert len(renderer.state.todo_items) == 2
        assert renderer.state.todo_items[0]["content"] == "Task A"
        assert renderer.state.todo_items[1]["content"] == "Task B"

    def test_handle_think_no_todo_list_no_update(self) -> None:
        """No update when todo_list is absent from broadcast."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "response": "text"})
        assert renderer._progress_tracker.total_count == 0
        assert renderer.state.todo_items == []

    def test_handle_think_empty_todo_list_clears(self) -> None:
        """Empty todo_list clears the progress tracker."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Set some todos first
        todos = [{"content": "Task 1", "status": "pending"}]
        renderer._handle_think(agent, {"done": False, "todo_list": todos})
        assert renderer._progress_tracker.total_count == 1

        # Empty list clears
        renderer._handle_think(agent, {"done": False, "todo_list": []})
        assert renderer._progress_tracker.total_count == 0

    def test_handle_think_todo_list_updates_in_real_time(self) -> None:
        """Progress updates as tasks complete across broadcasts."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Initial: 1 in_progress, 2 pending
        todos_v1 = [
            {"content": "Step 1", "status": "in_progress"},
            {"content": "Step 2", "status": "pending"},
            {"content": "Step 3", "status": "pending"},
        ]
        renderer._handle_think(agent, {"done": False, "todo_list": todos_v1})
        assert renderer._progress_tracker.completed_count == 0
        assert renderer._progress_tracker.current_task == "Step 1"

        # Update: step 1 completed, step 2 in_progress
        todos_v2 = [
            {"content": "Step 1", "status": "completed"},
            {"content": "Step 2", "status": "in_progress"},
            {"content": "Step 3", "status": "pending"},
        ]
        renderer._handle_think(agent, {"done": False, "todo_list": todos_v2})
        assert renderer._progress_tracker.completed_count == 1
        assert renderer._progress_tracker.current_task == "Step 2"

    def test_handle_think_done_with_todo_list(self) -> None:
        """todo_list is processed even when done=True."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        todos = [
            {"content": "Final task", "status": "completed"},
        ]
        renderer._handle_think(agent, {"done": True, "response": "done", "todo_list": todos})
        assert renderer._progress_tracker.completed_count == 1
        assert renderer._progress_tracker.total_count == 1

    def test_handle_think_todo_list_none_ignored(self) -> None:
        """Explicit None todo_list does not update progress tracker."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Set initial todos
        todos = [{"content": "Task", "status": "pending"}]
        renderer._handle_think(agent, {"done": False, "todo_list": todos})
        assert renderer._progress_tracker.total_count == 1

        # None should not clear
        renderer._handle_think(agent, {"done": False, "todo_list": None})
        assert renderer._progress_tracker.total_count == 1

    def test_handle_think_todo_list_non_list_ignored(self) -> None:
        """Non-list todo_list values are ignored."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_think(agent, {"done": False, "todo_list": "not a list"})
        assert renderer._progress_tracker.total_count == 0

    def test_progress_coexists_with_streaming(self) -> None:
        """Progress tracker and streaming text work together."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        todos = [{"content": "Working on it", "status": "in_progress"}]
        renderer._handle_think(
            agent,
            {"done": False, "response": "Processing...", "todo_list": todos},
        )
        assert renderer._stream_display.buffer == "Processing..."
        assert renderer._progress_tracker.total_count == 1


class TestProgressTrackerInRefreshDisplay:
    """Test that progress tracker appears in refresh display output."""

    def test_refresh_includes_progress_tracker(self) -> None:
        """Progress tracker table appears in Live display when todos exist."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()

        # Set some todos
        renderer._progress_tracker.update_todos(
            [
                {"content": "Task 1", "status": "completed"},
                {"content": "Task 2", "status": "in_progress"},
            ]
        )
        renderer._refresh_display()

        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        # Spinner + progress tracker = 2 renderables
        assert len(group.renderables) == 2

    def test_refresh_no_progress_when_empty(self) -> None:
        """No progress tracker renderable when no todos exist."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        # Only spinner, no progress tracker
        assert len(group.renderables) == 1

    def test_refresh_progress_above_status_line(self) -> None:
        """Progress tracker appears above status line in display order."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()

        # Set todos and status
        renderer._progress_tracker.update_todos(
            [
                {"content": "Working", "status": "in_progress"},
            ]
        )
        renderer._status_line.update(agent_id="agent-1", model="gpt-4", turn=1, max_turns=3)

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        # Spinner + progress + status = 3
        assert len(group.renderables) == 3

        # Last renderable should be status line (dimmed text with agent info)
        last = group.renderables[-1]
        assert "agent-1" in str(last)

        # Second-to-last should be the progress table
        from rich.table import Table

        progress = group.renderables[-2]
        assert isinstance(progress, Table)

    def test_refresh_all_components_together(self) -> None:
        """Spinner + stream + progress + status all render together."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        renderer._spinner.start()
        renderer._stream_display.append_chunk("Some text")
        renderer._progress_tracker.update_todos(
            [
                {"content": "Task", "status": "in_progress"},
            ]
        )
        renderer._status_line.update(agent_id="agent", model="model")

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        # Spinner + stream + progress + status = 4
        assert len(group.renderables) == 4

    def test_progress_only_when_spinner_stopped(self) -> None:
        """Progress tracker shows even when spinner is not running."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live
        # Spinner NOT started
        renderer._progress_tracker.update_todos(
            [
                {"content": "Task", "status": "pending"},
            ]
        )

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        assert len(group.renderables) == 1  # Only progress tracker


class TestResultPanelIntegration:
    """Test result panel creation and management through RichCLIRenderer handlers."""

    def _make_renderer(self) -> RichCLIRenderer:
        """Create a renderer with Live mocked to avoid terminal output."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        """Replace _ensure_live, _stop_live, _refresh_display with no-ops."""
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_handle_act_creates_result_panels(self) -> None:
        """Tool results in ACT broadcasts create ResultPanelComponent instances."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [
            {"function": "bash", "output": "file1.py\nfile2.py", "exit_code": 0},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        assert len(renderer.state.current_turn_results) == 1
        panel = renderer.state.current_turn_results[0]
        assert isinstance(panel, ResultPanelComponent)
        assert panel.tool_name == "bash"
        assert panel.output == "file1.py\nfile2.py"
        assert panel.exit_code == 0
        assert panel.is_recent is True

    def test_handle_act_creates_multiple_result_panels(self) -> None:
        """Multiple tool results create multiple ResultPanelComponents."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [
            {"function": "bash", "output": "output1", "exit_code": 0},
            {"function": "grep", "output": "output2", "exit_code": 0},
            {"function": "read_file", "output": "output3", "exit_code": 0},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        assert len(renderer.state.current_turn_results) == 3
        assert renderer.state.current_turn_results[0].tool_name == "bash"
        assert renderer.state.current_turn_results[1].tool_name == "grep"
        assert renderer.state.current_turn_results[2].tool_name == "read_file"

    def test_handle_act_no_results_no_panels(self) -> None:
        """No tool_results creates no result panels."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_act(agent, {"tool_calls": []})
        assert len(renderer.state.current_turn_results) == 0

    def test_handle_act_empty_results_no_panels(self) -> None:
        """Empty tool_results list creates no result panels."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_act(agent, {"tool_calls": [], "tool_results": []})
        assert len(renderer.state.current_turn_results) == 0

    def test_handle_act_skips_non_dict_results(self) -> None:
        """Non-dict items in tool_results are skipped."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [
            {"function": "bash", "output": "ok", "exit_code": 0},
            "not a dict",
            42,
            {"function": "grep", "output": "found", "exit_code": 0},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})
        assert len(renderer.state.current_turn_results) == 2

    def test_handle_act_uses_tool_key_fallback(self) -> None:
        """Falls back to 'tool' key when 'function' is not present."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [
            {"tool": "custom_tool", "output": "result", "exit_code": 0},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        assert len(renderer.state.current_turn_results) == 1
        assert renderer.state.current_turn_results[0].tool_name == "custom_tool"

    def test_handle_act_defaults_unknown_tool_name(self) -> None:
        """Defaults to 'unknown' when neither 'function' nor 'tool' present."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [{"output": "something", "exit_code": 0}]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        assert renderer.state.current_turn_results[0].tool_name == "unknown"

    def test_handle_act_defaults_exit_code_zero(self) -> None:
        """Default exit_code is 0 when not provided."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [{"function": "bash", "output": "ok"}]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        assert renderer.state.current_turn_results[0].exit_code == 0

    def test_handle_act_non_int_exit_code_defaults_zero(self) -> None:
        """Non-integer exit_code defaults to 0."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [{"function": "bash", "output": "ok", "exit_code": "error"}]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        assert renderer.state.current_turn_results[0].exit_code == 0

    def test_handle_act_accumulates_across_broadcasts(self) -> None:
        """Multiple ACT broadcasts accumulate result panels."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_act(
            agent,
            {"tool_calls": [], "tool_results": [{"function": "bash", "output": "o1"}]},
        )
        renderer._handle_act(
            agent,
            {"tool_calls": [], "tool_results": [{"function": "grep", "output": "o2"}]},
        )

        assert len(renderer.state.current_turn_results) == 2
        assert renderer.state.current_turn_results[0].tool_name == "bash"
        assert renderer.state.current_turn_results[1].tool_name == "grep"

    def test_new_results_are_recent(self) -> None:
        """All newly created result panels have is_recent=True."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [
            {"function": "bash", "output": "out1", "exit_code": 0},
            {"function": "grep", "output": "out2", "exit_code": 0},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        for panel in renderer.state.current_turn_results:
            assert panel.is_recent is True


class TestRecentToHistoricalTransition:
    """Test that current_turn_results transition to historical on new STAR loop."""

    def _make_renderer(self) -> RichCLIRenderer:
        renderer = RichCLIRenderer(console=Console(force_terminal=False))
        return renderer

    def _patch_live(self, renderer: RichCLIRenderer) -> None:
        renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
        renderer._stop_live = MagicMock()  # type: ignore[method-assign]
        renderer._refresh_display = MagicMock()  # type: ignore[method-assign]

    def test_see_moves_current_to_historical(self) -> None:
        """SEE phase moves current_turn_results to historical_results."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # Simulate ACT phase creating results
        tool_results = [
            {"function": "bash", "output": "output1", "exit_code": 0},
            {"function": "grep", "output": "output2", "exit_code": 0},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})
        assert len(renderer.state.current_turn_results) == 2
        assert len(renderer.state.historical_results) == 0

        # New STAR loop (SEE) transitions results
        renderer._handle_see(agent, {"caller_message": "new question"})
        assert len(renderer.state.current_turn_results) == 0
        assert len(renderer.state.historical_results) == 2

    def test_historical_panels_marked_not_recent(self) -> None:
        """Transitioned panels have is_recent=False."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [{"function": "bash", "output": "output", "exit_code": 0}]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})

        # Verify initially recent
        assert renderer.state.current_turn_results[0].is_recent is True

        # Transition
        renderer._handle_see(agent, {"caller_message": "next"})

        # Now historical - should be not recent
        assert renderer.state.historical_results[0].is_recent is False

    def test_selection_resets_on_transition(self) -> None:
        """selected_index resets to -1 when results transition to historical."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [
            {"function": "bash", "output": "o1"},
            {"function": "grep", "output": "o2"},
        ]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})
        renderer.state.selected_index = 1

        renderer._handle_see(agent, {"caller_message": "next"})
        assert renderer.state.selected_index == -1

    def test_expanded_indices_clear_on_transition(self) -> None:
        """expanded_indices clears when results transition to historical."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        tool_results = [{"function": "bash", "output": "o1"}]
        renderer._handle_act(agent, {"tool_calls": [], "tool_results": tool_results})
        renderer.state.expanded_indices.add(0)

        renderer._handle_see(agent, {"caller_message": "next"})
        assert len(renderer.state.expanded_indices) == 0

    def test_no_transition_when_no_current_results(self) -> None:
        """SEE with no current results doesn't add empty entries to historical."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        renderer._handle_see(agent, {"caller_message": "first"})
        assert len(renderer.state.historical_results) == 0
        assert len(renderer.state.current_turn_results) == 0

    def test_multiple_transitions_accumulate_history(self) -> None:
        """Multiple STAR loops accumulate historical results."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # First turn
        renderer._handle_act(
            agent,
            {"tool_calls": [], "tool_results": [{"function": "bash", "output": "turn1"}]},
        )
        assert len(renderer.state.current_turn_results) == 1

        # Second turn (transition first to historical)
        renderer._handle_see(agent, {"caller_message": "q2"})
        renderer._handle_act(
            agent,
            {"tool_calls": [], "tool_results": [{"function": "grep", "output": "turn2"}]},
        )
        assert len(renderer.state.historical_results) == 1
        assert len(renderer.state.current_turn_results) == 1

        # Third turn (transition both to historical)
        renderer._handle_see(agent, {"caller_message": "q3"})
        assert len(renderer.state.historical_results) == 2
        assert len(renderer.state.current_turn_results) == 0

    def test_historical_order_preserved(self) -> None:
        """Historical results maintain chronological order across transitions."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # First turn - 2 results
        renderer._handle_act(
            agent,
            {
                "tool_calls": [],
                "tool_results": [
                    {"function": "bash", "output": "first"},
                    {"function": "grep", "output": "second"},
                ],
            },
        )

        # Second turn - 1 result
        renderer._handle_see(agent, {"caller_message": "q2"})
        renderer._handle_act(
            agent,
            {"tool_calls": [], "tool_results": [{"function": "read_file", "output": "third"}]},
        )

        # Third turn - transition all
        renderer._handle_see(agent, {"caller_message": "q3"})

        # Historical should have all 3 in order
        assert len(renderer.state.historical_results) == 3
        assert renderer.state.historical_results[0].tool_name == "bash"
        assert renderer.state.historical_results[1].tool_name == "grep"
        assert renderer.state.historical_results[2].tool_name == "read_file"

    def test_full_star_loop_with_results(self) -> None:
        """Verify complete STAR loop creates and transitions result panels."""
        renderer = self._make_renderer()
        self._patch_live(renderer)
        agent = _FakeAgent()

        # First STAR loop
        renderer._handle_see(agent, {"caller_message": "hello"})
        renderer._handle_think(
            agent,
            {"done": False, "tool_calls": [{"function": "bash", "arguments": {"command": "ls"}}]},
        )
        renderer._handle_act(
            agent,
            {
                "tool_calls": [{"function": "bash"}],
                "tool_results": [{"function": "bash", "output": "file1.py", "exit_code": 0}],
            },
        )
        renderer._handle_think(agent, {"done": True, "response": "Found files"})

        # Results are current
        assert len(renderer.state.current_turn_results) == 1
        assert renderer.state.current_turn_results[0].is_recent is True

        # Second STAR loop starts - transition
        renderer._handle_see(agent, {"caller_message": "next question"})
        assert len(renderer.state.current_turn_results) == 0
        assert len(renderer.state.historical_results) == 1
        assert renderer.state.historical_results[0].is_recent is False


class TestResultPanelsInRefreshDisplay:
    """Test that result panels appear in refresh display output."""

    def test_refresh_includes_current_turn_results(self) -> None:
        """Current turn result panels appear in Live display."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        # Add a current turn result
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        renderer.state.current_turn_results.append(panel)

        renderer._refresh_display()

        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        assert len(group.renderables) == 1  # Just the result panel

    def test_refresh_includes_historical_results(self) -> None:
        """Historical result panels appear in Live display."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        panel = ResultPanelComponent(tool_name="bash", output="old", is_recent=False)
        renderer.state.historical_results.append(panel)

        renderer._refresh_display()

        mock_live.update.assert_called_once()
        group = mock_live.update.call_args[0][0]
        assert hasattr(group, "renderables")
        assert len(group.renderables) == 1

    def test_refresh_historical_before_recent(self) -> None:
        """Historical results render before recent results in display."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        # Add historical
        hist = ResultPanelComponent(tool_name="old_bash", output="old", is_recent=False)
        renderer.state.historical_results.append(hist)

        # Add current
        curr = ResultPanelComponent(tool_name="new_bash", output="new", is_recent=True)
        renderer.state.current_turn_results.append(curr)

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        renderables = group.renderables
        assert len(renderables) == 2

        # First should be historical (dim border)
        assert renderables[0].border_style == "dim"
        # Second should be recent (cyan border)
        assert renderables[1].border_style == "cyan"

    def test_refresh_historical_always_collapsed(self) -> None:
        """Historical results are always rendered collapsed."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        # Short output that would normally be expanded by default
        hist = ResultPanelComponent(tool_name="bash", output="short", is_recent=False)
        renderer.state.historical_results.append(hist)

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        panel = group.renderables[0]
        # Collapsed summary should contain the tool_name summary text
        body_text = str(panel.renderable)
        assert "bash -> exit code" in body_text

    def test_refresh_recent_uses_selection_state(self) -> None:
        """Recent results use selected_index for highlight."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        p0 = ResultPanelComponent(tool_name="bash", output="o1", is_recent=True)
        p1 = ResultPanelComponent(tool_name="grep", output="o2", is_recent=True)
        renderer.state.current_turn_results = [p0, p1]
        renderer.state.selected_index = 1

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        panels = group.renderables
        # First panel: not selected (cyan)
        assert panels[0].border_style == "cyan"
        # Second panel: selected (bold yellow)
        assert panels[1].border_style == "bold yellow"

    def test_refresh_recent_uses_expanded_indices(self) -> None:
        """Recent results use expanded_indices for expand state."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        # Long output (>= 10 lines) - would be collapsed by default
        long_output = "\n".join(f"line {i}" for i in range(20))
        p0 = ResultPanelComponent(tool_name="bash", output=long_output, is_recent=True)
        renderer.state.current_turn_results = [p0]
        renderer.state.expanded_indices = {0}  # Force expanded

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        panel = group.renderables[0]
        # Expanded panel should show the actual output (not summary)
        body_text = str(panel.renderable)
        assert "line 0" in body_text
        assert "line 19" in body_text

    def test_refresh_all_components_with_results(self) -> None:
        """All components render together: spinner + stream + results + progress + status."""
        renderer = RichCLIRenderer(console=Console(force_terminal=False))

        mock_live = MagicMock()
        renderer._live = mock_live

        renderer._spinner.start()
        renderer._stream_display.append_chunk("Streaming...")

        hist = ResultPanelComponent(tool_name="old", output="old", is_recent=False)
        renderer.state.historical_results.append(hist)
        curr = ResultPanelComponent(tool_name="new", output="new", is_recent=True)
        renderer.state.current_turn_results.append(curr)

        renderer._progress_tracker.update_todos([{"content": "Task", "status": "in_progress"}])
        renderer._status_line.update(agent_id="agent", model="model")

        renderer._refresh_display()

        group = mock_live.update.call_args[0][0]
        # spinner + stream + historical + current + progress + status = 6
        assert len(group.renderables) == 6
