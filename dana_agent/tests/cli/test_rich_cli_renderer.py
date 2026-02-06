"""Tests for RichCLIRenderer message routing."""

from unittest.mock import patch

from rich.console import Console

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
