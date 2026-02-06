"""Integration tests for RichCLIRenderer with the Notifier/broadcast system.

Verifies that RichCLIRenderer integrates seamlessly with agents using
the Notifier base class, works alongside ThoughtLogger, and correctly
renders a complete STAR loop conversation simulation.
"""

from unittest.mock import MagicMock

from rich.console import Console

from dana.apps.dana.thought_logger import ThoughtLogger
from dana.cli.rich_cli_renderer import RichCLIRenderer
from dana.common.protocols.notifiable import Notifier


class _FakeNotifierAgent(Notifier):
    """Minimal agent using the real Notifier base class for integration testing.

    Simulates an agent that broadcasts STAR loop messages.
    Has the attributes RichCLIRenderer expects on a notifier object.
    """

    def __init__(
        self,
        object_id: str = "dana-coding-agent",
        model: str = "claude-sonnet-4-5-20250929",
        star_loop_count: int = 0,
        max_turns: int = 5,
    ) -> None:
        super().__init__()
        self.object_id = object_id
        self.agent_type = "star"
        self.llm_client = type("LLMClient", (), {"model": model})()
        self._star_loop_count = star_loop_count
        self.max_turns = max_turns


def _make_renderer() -> RichCLIRenderer:
    """Create a RichCLIRenderer with mocked Live context for testing."""
    renderer = RichCLIRenderer(console=Console(force_terminal=True))
    renderer._ensure_live = MagicMock()  # type: ignore[method-assign]
    renderer._stop_live = MagicMock()  # type: ignore[method-assign]
    renderer._refresh_display = MagicMock()  # type: ignore[method-assign]
    return renderer


class TestWithNotifiableAttachment:
    """Test that RichCLIRenderer attaches via agent.with_notifiable()."""

    def test_attach_renderer_returns_agent(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        result = agent.with_notifiable(renderer)
        assert result is agent

    def test_renderer_is_registered(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        agent.with_notifiable(renderer)
        assert renderer in agent._notifiables

    def test_multiple_notifiables(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        logger = ThoughtLogger(verbose=False, show_tool_calls=False)
        agent.with_notifiable(renderer, logger)
        assert renderer in agent._notifiables
        assert logger in agent._notifiables

    def test_method_chaining(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        logger = ThoughtLogger(verbose=False, show_tool_calls=False)
        result = agent.with_notifiable(renderer).with_notifiable(logger)
        assert result is agent
        assert len(agent._notifiables) == 2


class TestBroadcastToRenderer:
    """Test that agent.broadcast() triggers renderer.notify()."""

    def test_broadcast_triggers_notify(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        agent.broadcast({"trace_percepts": {"caller_message": "hello"}})
        assert renderer.state.current_phase == "SEE"

    def test_broadcast_updates_agent_context(self) -> None:
        agent = _FakeNotifierAgent(
            object_id="my-agent",
            model="gpt-4",
            star_loop_count=2,
            max_turns=10,
        )
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        agent.broadcast({"trace_percepts": {"caller_message": "test"}})
        assert renderer.state.current_agent_id == "my-agent"
        assert renderer.state.current_model == "gpt-4"
        assert renderer.state.current_turn == 2
        assert renderer.state.max_turns == 10

    def test_broadcast_with_empty_message(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        # Empty message should not crash
        agent.broadcast({})
        assert renderer.state.current_agent_id == "dana-coding-agent"


class TestAlongsideThoughtLogger:
    """Test that RichCLIRenderer works alongside ThoughtLogger without interference."""

    def test_both_receive_broadcasts(self) -> None:
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        logger = ThoughtLogger(verbose=False, show_tool_calls=False)
        agent.with_notifiable(renderer, logger)

        agent.broadcast({"trace_percepts": {"caller_message": "hello"}})
        # Renderer received and processed (state updated)
        assert renderer.state.current_phase == "SEE"
        # ThoughtLogger didn't crash (verbose=False so it skipped display)

    def test_renderer_error_does_not_break_logger(self) -> None:
        """Notifier catches exceptions so one notifiable failure doesn't affect others."""
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        logger = ThoughtLogger(verbose=False, show_tool_calls=False)

        # Make renderer throw an exception
        call_count = {"logger_calls": 0}
        original_logger_notify = logger.notify

        def tracking_logger_notify(n: object, m: dict) -> None:  # type: ignore[type-arg]
            call_count["logger_calls"] += 1
            original_logger_notify(n, m)

        logger.notify = tracking_logger_notify  # type: ignore[method-assign,assignment]

        def failing_notify(_notifier: object, _message: dict) -> None:  # type: ignore[type-arg]
            raise RuntimeError("Simulated renderer failure")

        renderer.notify = failing_notify  # type: ignore[method-assign,assignment]

        # Renderer registered first, logger second
        agent.with_notifiable(renderer, logger)
        agent.broadcast({"trace_percepts": {"caller_message": "hello"}})

        # Logger should still have been called despite renderer failure
        assert call_count["logger_calls"] == 1

    def test_no_changes_required_to_agent(self) -> None:
        """Agent uses standard Notifier.broadcast() - no custom code needed."""
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()
        logger = ThoughtLogger(verbose=False, show_tool_calls=False)

        # Standard Notifier API - no DanaCodingAgent-specific code
        agent.with_notifiable(renderer, logger)
        agent.broadcast({"trace_thoughts": {"done": False, "response": "thinking..."}})

        assert renderer.state.current_phase == "THINK"


class TestFullConversationSimulation:
    """Integration test simulating a complete multi-turn STAR loop conversation."""

    def test_complete_star_loop(self) -> None:
        """Simulate a full SEE → THINK → ACT → THINK(done) cycle."""
        agent = _FakeNotifierAgent(star_loop_count=1)
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        # SEE: User message arrives
        agent.broadcast({"trace_percepts": {"caller_message": "List files in current directory"}})
        assert renderer.state.current_phase == "SEE"
        assert renderer._spinner.running is True

        # THINK: Agent decides to use bash tool
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": False,
                    "response": "",
                    "reasoning": "I'll list the files using ls command",
                    "tool_calls": [{"function": "bash", "arguments": {"command": "ls -la"}}],
                }
            }
        )
        assert renderer.state.current_phase == "THINK"
        assert len(renderer._pending_tool_cards) == 1

        # ACT: Tool execution results
        agent.broadcast(
            {
                "trace_outputs": {
                    "tool_calls": [{"function": "bash", "arguments": {"command": "ls -la"}}],
                    "tool_results": [
                        {
                            "function": "bash",
                            "output": "total 16\ndrwxr-xr-x  4 user  group  128 Jan  1 12:00 .\n-rw-r--r--  1 user  group  256 Jan  1 12:00 file.py",
                            "exit_code": 0,
                        }
                    ],
                }
            }
        )
        assert renderer.state.current_phase == "ACT"
        assert len(renderer.state.current_turn_results) == 1
        assert renderer.state.current_turn_results[0].tool_name == "bash"
        assert renderer.state.current_turn_results[0].exit_code == 0
        assert renderer.state.current_turn_results[0].is_recent is True

        # THINK (done): Agent provides final answer
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": True,
                    "response": "Here are the files in your directory...",
                }
            }
        )
        assert renderer.state.current_phase == "THINK"
        assert renderer._spinner.running is False

    def test_multi_tool_star_loop(self) -> None:
        """Simulate a STAR loop with multiple tool calls."""
        agent = _FakeNotifierAgent(star_loop_count=1)
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        # SEE
        agent.broadcast({"trace_percepts": {"caller_message": "Find and read the config file"}})

        # THINK: Multiple tools
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": False,
                    "response": "",
                    "tool_calls": [
                        {"function": "glob", "arguments": {"pattern": "**/*.toml"}},
                        {"function": "read_file", "arguments": {"path": "pyproject.toml"}},
                    ],
                }
            }
        )
        assert len(renderer._pending_tool_cards) == 2

        # ACT: Multiple results
        agent.broadcast(
            {
                "trace_outputs": {
                    "tool_calls": [
                        {"function": "glob", "arguments": {"pattern": "**/*.toml"}},
                        {"function": "read_file", "arguments": {"path": "pyproject.toml"}},
                    ],
                    "tool_results": [
                        {"function": "glob", "output": "pyproject.toml\nsetup.toml", "exit_code": 0},
                        {"function": "read_file", "output": "[project]\nname = 'test'", "exit_code": 0},
                    ],
                }
            }
        )
        assert len(renderer.state.current_turn_results) == 2

        # THINK (done)
        agent.broadcast({"trace_thoughts": {"done": True, "response": "Found config."}})
        assert renderer._spinner.running is False

    def test_multi_turn_conversation(self) -> None:
        """Simulate multiple user messages (turns) with result transitions."""
        agent = _FakeNotifierAgent(star_loop_count=1)
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        # --- Turn 1 ---
        agent.broadcast({"trace_percepts": {"caller_message": "Check git status"}})
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": False,
                    "tool_calls": [{"function": "bash", "arguments": {"command": "git status"}}],
                }
            }
        )
        agent.broadcast(
            {
                "trace_outputs": {
                    "tool_results": [{"function": "bash", "output": "On branch main", "exit_code": 0}],
                }
            }
        )
        agent.broadcast({"trace_thoughts": {"done": True, "response": "You're on main branch."}})

        assert len(renderer.state.current_turn_results) == 1
        assert len(renderer.state.historical_results) == 0

        # --- Turn 2 ---
        agent._star_loop_count = 2
        agent.broadcast({"trace_percepts": {"caller_message": "Now show me the diff"}})

        # Turn 1 results should have transitioned to historical
        assert len(renderer.state.historical_results) == 1
        assert renderer.state.historical_results[0].is_recent is False
        assert len(renderer.state.current_turn_results) == 0

        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": False,
                    "tool_calls": [{"function": "bash", "arguments": {"command": "git diff"}}],
                }
            }
        )
        agent.broadcast(
            {
                "trace_outputs": {
                    "tool_results": [{"function": "bash", "output": "diff --git a/file.py", "exit_code": 0}],
                }
            }
        )
        agent.broadcast({"trace_thoughts": {"done": True, "response": "Here's the diff."}})

        assert len(renderer.state.current_turn_results) == 1
        assert len(renderer.state.historical_results) == 1

    def test_star_loop_with_todos(self) -> None:
        """Simulate a STAR loop with todo list progress tracking."""
        agent = _FakeNotifierAgent(star_loop_count=1)
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        agent.broadcast({"trace_percepts": {"caller_message": "Implement feature X"}})

        # THINK with todo list
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": False,
                    "response": "",
                    "tool_calls": [{"function": "write_file", "arguments": {"path": "feature.py"}}],
                    "todo_list": [
                        {"content": "Create feature module", "status": "in_progress"},
                        {"content": "Write tests", "status": "pending"},
                        {"content": "Update docs", "status": "pending"},
                    ],
                }
            }
        )
        assert renderer._progress_tracker.total_count == 3
        assert renderer._progress_tracker.completed_count == 0
        assert renderer.state.todo_items == [
            {"content": "Create feature module", "status": "in_progress"},
            {"content": "Write tests", "status": "pending"},
            {"content": "Update docs", "status": "pending"},
        ]

        # ACT
        agent.broadcast(
            {
                "trace_outputs": {
                    "tool_results": [{"function": "write_file", "output": "Written", "exit_code": 0}],
                }
            }
        )

        # THINK with updated todos
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": False,
                    "response": "",
                    "tool_calls": [{"function": "write_file", "arguments": {"path": "test_feature.py"}}],
                    "todo_list": [
                        {"content": "Create feature module", "status": "completed"},
                        {"content": "Write tests", "status": "in_progress"},
                        {"content": "Update docs", "status": "pending"},
                    ],
                }
            }
        )
        assert renderer._progress_tracker.completed_count == 1

    def test_star_loop_with_streaming_response(self) -> None:
        """Simulate streaming response chunks during THINK phase."""
        agent = _FakeNotifierAgent(star_loop_count=1)
        renderer = _make_renderer()
        agent.with_notifiable(renderer)

        agent.broadcast({"trace_percepts": {"caller_message": "Explain Python decorators"}})

        # Streaming chunks
        agent.broadcast({"trace_thoughts": {"done": False, "response": "A decorator"}})
        assert renderer._stream_display.buffer == "A decorator"

        agent.broadcast({"trace_thoughts": {"done": False, "response": " is a function"}})
        assert renderer._stream_display.buffer == "A decorator is a function"

        agent.broadcast({"trace_thoughts": {"done": False, "response": " that wraps another function."}})
        assert "wraps another function" in renderer._stream_display.buffer

        # Done
        agent.broadcast(
            {
                "trace_thoughts": {
                    "done": True,
                    "response": "A decorator is a function that wraps another function.",
                }
            }
        )
        assert renderer._spinner.running is False


class TestSubagentSimulation:
    """Test subagent transitions through broadcast messages."""

    def test_subagent_transition(self) -> None:
        """Simulate parent agent spawning a subagent."""
        parent = _FakeNotifierAgent(object_id="parent-agent")
        renderer = _make_renderer()
        parent.with_notifiable(renderer)

        # Parent broadcasts
        parent.broadcast({"trace_percepts": {"caller_message": "Do complex task"}})
        assert renderer.state.current_agent_id == "parent-agent"

        # Simulate subagent by using a different notifier with different object_id
        child = _FakeNotifierAgent(object_id="child-agent", model="gpt-4")

        # When child broadcasts to renderer directly (simulating subagent notification)
        renderer.notify(child, {"trace_percepts": {"perception": "Subagent started"}})
        assert renderer.state.current_agent_id == "child-agent"
        assert len(renderer._agent_stack) == 1
        assert renderer._agent_stack[0] == "parent-agent"

        # Child completes, parent resumes
        renderer.notify(parent, {"trace_thoughts": {"done": True, "response": "Done."}})
        assert renderer.state.current_agent_id == "parent-agent"
        assert len(renderer._agent_stack) == 0


class TestRendererDoesNotRequireAgentChanges:
    """Verify no changes are needed to the agent code - standard Notifier protocol works."""

    def test_standard_notifier_api(self) -> None:
        """RichCLIRenderer uses only standard Notifier protocol methods."""
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()

        # Only standard Notifier API used
        agent.with_notifiable(renderer)
        agent.broadcast({"trace_percepts": {"caller_message": "test"}})
        agent.broadcast({"trace_thoughts": {"done": True, "response": "done"}})

        # Verify it worked
        assert renderer.state.current_agent_id == "dana-coding-agent"

    def test_remove_notifiable(self) -> None:
        """RichCLIRenderer can be removed via standard Notifier API."""
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()

        agent.with_notifiable(renderer)
        assert renderer in agent._notifiables

        removed = agent.remove_notifiable(renderer)
        assert removed is True
        assert renderer not in agent._notifiables

    def test_add_notifier_alternative(self) -> None:
        """RichCLIRenderer can be added via add_notifier() as well."""
        agent = _FakeNotifierAgent()
        renderer = _make_renderer()

        agent.add_notifier(renderer)
        assert renderer in agent._notifiables

        agent.broadcast({"trace_percepts": {"caller_message": "test"}})
        assert renderer.state.current_phase == "SEE"
