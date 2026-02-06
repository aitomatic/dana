"""Tests for ToolCardComponent tool invocation display."""

from rich.panel import Panel
from rich.text import Text

from dana.cli.components.tool_card import ToolCardComponent


class TestRenderBasic:
    """Test basic rendering for different tool types."""

    def test_render_returns_panel(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "bash", "arguments": {"command": "ls"}})
        assert isinstance(result, Panel)

    def test_render_unknown_function(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "unknown_tool", "arguments": {"key": "val"}})
        assert isinstance(result, Panel)
        assert "unknown_tool" in str(result.title)

    def test_render_empty_tool_call(self) -> None:
        card = ToolCardComponent()
        result = card.render({})
        assert isinstance(result, Panel)
        assert "unknown" in str(result.title)


class TestBashToolCard:
    """Test bash tool card rendering."""

    def test_bash_icon(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "bash", "arguments": {"command": "ls -la"}})
        title = str(result.title)
        assert "🔧" in title
        assert "bash" in title

    def test_bash_shows_command(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "bash", "arguments": {"command": "ls -la"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "ls -la" in body.plain

    def test_bash_truncates_long_command(self) -> None:
        long_cmd = "x" * 150
        card = ToolCardComponent()
        result = card.render({"function": "bash", "arguments": {"command": long_cmd}})
        body = result.renderable
        assert isinstance(body, Text)
        assert len(body.plain) <= 101 + 1  # 100 chars + ellipsis
        assert body.plain.endswith("…")

    def test_bash_no_command(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "bash", "arguments": {}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "(no command)" in body.plain

    def test_shell_classified_as_bash(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "shell", "arguments": {"command": "echo hi"}})
        assert "🔧" in str(result.title)

    def test_execute_classified_as_bash(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "execute", "arguments": {"command": "pwd"}})
        assert "🔧" in str(result.title)


class TestFileIOToolCard:
    """Test file-io tool card rendering."""

    def test_file_io_icon(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "read_file", "arguments": {"path": "/tmp/test.py"}})
        title = str(result.title)
        assert "📁" in title
        assert "read_file" in title

    def test_file_io_shows_path(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "write_file", "arguments": {"path": "/tmp/out.txt"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "/tmp/out.txt" in body.plain

    def test_file_io_uses_file_path_key(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "read", "arguments": {"file_path": "/src/main.py"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "/src/main.py" in body.plain

    def test_file_io_no_path(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "edit_file", "arguments": {}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "(no path)" in body.plain

    def test_glob_classified_as_file_io(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "glob", "arguments": {"path": "*.py"}})
        assert "📁" in str(result.title)


class TestSearchToolCard:
    """Test search tool card rendering."""

    def test_search_icon(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "search", "arguments": {"pattern": "def main"}})
        title = str(result.title)
        assert "🔍" in title
        assert "search" in title

    def test_search_shows_pattern_and_path(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "grep", "arguments": {"pattern": "TODO", "path": "/src"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "pattern: TODO" in body.plain
        assert "path: /src" in body.plain

    def test_search_pattern_only(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "search", "arguments": {"pattern": "error"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "pattern: error" in body.plain

    def test_search_no_params(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "search", "arguments": {}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "(no params)" in body.plain

    def test_find_classified_as_search(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "find", "arguments": {"pattern": "*.py"}})
        assert "🔍" in str(result.title)


class TestTaskToolCard:
    """Test task tool card rendering."""

    def test_task_icon(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "task", "arguments": {"agent_id": "coder", "prompt": "Fix bug"}})
        title = str(result.title)
        assert "🤖" in title
        assert "task" in title

    def test_task_shows_agent_and_prompt(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "task", "arguments": {"agent_id": "coder", "prompt": "Fix bug"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "agent: coder" in body.plain
        assert "prompt: Fix bug" in body.plain

    def test_task_truncates_long_prompt(self) -> None:
        long_prompt = "A" * 80
        card = ToolCardComponent()
        result = card.render({"function": "task", "arguments": {"agent_id": "coder", "prompt": long_prompt}})
        body = result.renderable
        assert isinstance(body, Text)
        # prompt should be truncated to 50 chars + ellipsis
        assert "A" * 50 + "…" in body.plain

    def test_task_uses_agent_type_key(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "agent", "arguments": {"agent_type": "reviewer"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "agent: reviewer" in body.plain

    def test_task_no_params(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "task", "arguments": {}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "(no params)" in body.plain


class TestClassification:
    """Test tool type classification."""

    def test_default_icon_for_unknown(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "custom_tool", "arguments": {}})
        assert "⚡" in str(result.title)

    def test_other_type_shows_all_args(self) -> None:
        card = ToolCardComponent()
        result = card.render({"function": "custom", "arguments": {"a": 1, "b": "two"}})
        body = result.renderable
        assert isinstance(body, Text)
        assert "a=1" in body.plain
        assert "b=two" in body.plain


class TestImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import ToolCardComponent as Imported

        assert Imported is ToolCardComponent
