"""Tests for SubagentCardComponent rendering and state tracking."""

import time

from rich.console import Group

from dana.cli.components.subagent_card import SubagentCardComponent


class TestSubagentCardInit:
    """Test constructor and defaults."""

    def test_initial_state(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="Find files")
        assert card.agent_type == "Explore"
        assert card.purpose == "Find files"
        assert card.tool_calls == []
        assert card.tool_results == []
        assert card.is_complete is False
        assert card.completion_time is None

    def test_tool_count_initially_zero(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        assert card.tool_count == 0


class TestAddToolCall:
    """Test adding tool calls."""

    def test_add_single_tool_call(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        tc = {"function": "grep", "arguments": {"pattern": "foo"}}
        card.add_tool_call(tc)
        assert card.tool_count == 1
        assert card.tool_calls[0] == tc

    def test_add_multiple_tool_calls(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        for i in range(10):
            card.add_tool_call({"function": f"tool_{i}", "arguments": {}})
        assert card.tool_count == 10


class TestAddToolResult:
    """Test adding tool results."""

    def test_add_tool_result(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        result = {"target": "grep", "result": "found 3 matches", "success": True}
        card.add_tool_result(result)
        assert len(card.tool_results) == 1


class TestComplete:
    """Test completion."""

    def test_complete_marks_done(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.complete()
        assert card.is_complete is True
        assert card.completion_time is not None

    def test_complete_records_time(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.complete()
        assert card.completion_time is not None
        assert card.completion_time >= card.start_time


class TestElapsedText:
    """Test elapsed time formatting."""

    def test_short_duration(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.start_time = time.time() - 5
        text = card.elapsed_text
        assert text == "5s" or text == "4s"  # Allow small timing variance

    def test_long_duration(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.start_time = time.time() - 90
        text = card.elapsed_text
        assert text.startswith("1m")

    def test_completed_duration_frozen(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.start_time = time.time() - 10
        card.complete()
        text1 = card.elapsed_text
        # Should be frozen at completion time, not growing
        assert "10s" in text1 or "9s" in text1 or "11s" in text1


class TestFormatLastTool:
    """Test _format_last_tool for different tool types."""

    def test_grep_tool(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.add_tool_call({"function": "grep", "arguments": {"pattern": "foo", "path": "/src"}})
        result = card._format_last_tool()
        assert 'pattern: "foo"' in result
        assert 'path: "/src"' in result

    def test_read_tool(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.add_tool_call({"function": "read", "arguments": {"file_path": "/tmp/test.py"}})
        result = card._format_last_tool()
        assert "/tmp/test.py" in result

    def test_glob_tool(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.add_tool_call({"function": "glob", "arguments": {"pattern": "**/*.py"}})
        result = card._format_last_tool()
        assert "**/*.py" in result

    def test_bash_tool_truncated(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        long_cmd = "x" * 50
        card.add_tool_call({"function": "bash", "arguments": {"command": long_cmd}})
        result = card._format_last_tool()
        assert len(result) < 60  # Should be truncated

    def test_unknown_tool(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.add_tool_call({"function": "custom_tool", "arguments": {}})
        result = card._format_last_tool()
        assert result == "custom_tool"

    def test_no_tool_calls(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        assert card._format_last_tool() == ""


class TestRender:
    """Test Rich rendering."""

    def test_render_empty_card(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        result = card.render()
        assert isinstance(result, Group)

    def test_render_in_progress_with_tools(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="Find files")
        card.add_tool_call({"function": "grep", "arguments": {"pattern": "foo"}})
        card.add_tool_call({"function": "read", "arguments": {"file_path": "/a.py"}})
        card.add_tool_call({"function": "glob", "arguments": {"pattern": "*.py"}})
        result = card.render()
        assert isinstance(result, Group)
        # Should have header + last tool + "+N more" lines
        assert len(result.renderables) == 3

    def test_render_completed(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        for i in range(5):
            card.add_tool_call({"function": f"tool_{i}", "arguments": {}})
        card.complete()
        result = card.render()
        assert isinstance(result, Group)
        # Header + "Done (5 tool uses in Xs)" = 2 lines
        assert len(result.renderables) == 2

    def test_render_expanded(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        for i in range(3):
            card.add_tool_call({"function": f"tool_{i}", "arguments": {}})
        result = card.render(expanded=True)
        assert isinstance(result, Group)
        # Header + 3 tool lines = 4
        assert len(result.renderables) == 4

    def test_render_single_tool_no_more_line(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.add_tool_call({"function": "grep", "arguments": {"pattern": "foo"}})
        result = card.render()
        assert isinstance(result, Group)
        # Header + last tool = 2 (no "+N more" line for single tool)
        assert len(result.renderables) == 2


class TestRenderPlain:
    """Test plain text rendering for no-color terminals."""

    def test_render_plain_empty(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        text = card.render_plain()
        assert "Explore" in text
        assert "test" in text

    def test_render_plain_with_tools(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        card.add_tool_call({"function": "grep", "arguments": {"pattern": "foo"}})
        card.add_tool_call({"function": "read", "arguments": {}})
        text = card.render_plain()
        assert "+1 more tool uses" in text

    def test_render_plain_completed(self) -> None:
        card = SubagentCardComponent(agent_type="Explore", purpose="test")
        for i in range(10):
            card.add_tool_call({"function": f"tool_{i}", "arguments": {}})
        card.complete()
        text = card.render_plain()
        assert "Done" in text
        assert "10 tool uses" in text


class TestImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import SubagentCardComponent as Imported

        assert Imported is SubagentCardComponent
