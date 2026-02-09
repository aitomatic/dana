"""Tests for ResultPanelComponent tool result display with collapse/expand."""

from rich.panel import Panel
from rich.text import Text

from dana.cli.components.result_panel import ResultPanelComponent


class TestInit:
    """Test ResultPanelComponent initialization."""

    def test_stores_tool_name(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello", exit_code=0)
        assert panel.tool_name == "bash"

    def test_stores_output(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello world")
        assert panel.output == "hello world"

    def test_stores_exit_code(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="", exit_code=1)
        assert panel.exit_code == 1

    def test_default_exit_code_zero(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="")
        assert panel.exit_code == 0

    def test_default_is_recent(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="")
        assert panel.is_recent is True

    def test_is_recent_false(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="", is_recent=False)
        assert panel.is_recent is False


class TestLineCount:
    """Test line counting."""

    def test_empty_output_zero_lines(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="")
        assert panel.line_count == 0

    def test_single_line(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello")
        assert panel.line_count == 1

    def test_multiple_lines(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2\nline3")
        assert panel.line_count == 3

    def test_trailing_newline(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2\n")
        assert panel.line_count == 3  # split gives ["line1", "line2", ""]


class TestDefaultExpanded:
    """Test default expand/collapse state."""

    def test_short_output_expanded(self) -> None:
        output = "\n".join(f"line {i}" for i in range(5))
        panel = ResultPanelComponent(tool_name="bash", output=output)
        assert panel.default_expanded is True

    def test_nine_lines_expanded(self) -> None:
        output = "\n".join(f"line {i}" for i in range(9))
        panel = ResultPanelComponent(tool_name="bash", output=output)
        assert panel.default_expanded is True

    def test_ten_lines_collapsed(self) -> None:
        output = "\n".join(f"line {i}" for i in range(10))
        panel = ResultPanelComponent(tool_name="bash", output=output)
        assert panel.default_expanded is False

    def test_many_lines_collapsed(self) -> None:
        output = "\n".join(f"line {i}" for i in range(50))
        panel = ResultPanelComponent(tool_name="bash", output=output)
        assert panel.default_expanded is False

    def test_empty_output_expanded(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="")
        assert panel.default_expanded is True


class TestRenderExpanded:
    """Test expanded rendering."""

    def test_render_returns_panel(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello")
        result = panel.render(expanded=True)
        assert isinstance(result, Panel)

    def test_expanded_shows_full_output(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="full output text")
        result = panel.render(expanded=True)
        body = result.renderable
        assert isinstance(body, Text)
        assert "full output text" in body.plain

    def test_expanded_shows_tool_name_title(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello")
        result = panel.render(expanded=True)
        assert "bash" in str(result.title)

    def test_expanded_empty_output(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="")
        result = panel.render(expanded=True)
        body = result.renderable
        assert isinstance(body, Text)
        assert body.plain == ""


class TestRenderCollapsed:
    """Test collapsed rendering."""

    def test_collapsed_shows_summary(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2", exit_code=0)
        result = panel.render(expanded=False)
        body = result.renderable
        assert isinstance(body, Text)
        assert "bash" in body.plain
        assert "exit code 0" in body.plain
        assert "2 lines" in body.plain

    def test_collapsed_summary_format(self) -> None:
        panel = ResultPanelComponent(tool_name="grep", output="match1\nmatch2\nmatch3", exit_code=1)
        result = panel.render(expanded=False)
        body = result.renderable
        assert isinstance(body, Text)
        assert "grep -> exit code 1, 3 lines" in body.plain

    def test_collapsed_has_dim_style(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello")
        result = panel.render(expanded=False)
        body = result.renderable
        assert isinstance(body, Text)
        assert body.style == "dim"


class TestRenderDefaultExpand:
    """Test rendering with default expand state."""

    def test_short_output_defaults_expanded(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="short")
        result = panel.render()  # No expanded param
        body = result.renderable
        assert isinstance(body, Text)
        assert "short" in body.plain
        # Should not be a summary since < 10 lines
        assert "exit code" not in body.plain

    def test_long_output_defaults_collapsed(self) -> None:
        output = "\n".join(f"line {i}" for i in range(20))
        panel = ResultPanelComponent(tool_name="bash", output=output, exit_code=0)
        result = panel.render()  # No expanded param
        body = result.renderable
        assert isinstance(body, Text)
        assert "exit code 0" in body.plain
        assert "20 lines" in body.plain


class TestRecentVsHistorical:
    """Test visual distinction between recent and historical panels."""

    def test_recent_panel_has_cyan_border(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        result = panel.render(expanded=True)
        assert result.border_style == "cyan"

    def test_historical_panel_has_dim_border(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=False)
        result = panel.render(expanded=True)
        assert result.border_style == "dim"

    def test_recent_collapsed_has_cyan_border(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        result = panel.render(expanded=False)
        assert result.border_style == "cyan"

    def test_historical_collapsed_has_dim_border(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=False)
        result = panel.render(expanded=False)
        assert result.border_style == "dim"

    def test_transition_recent_to_historical(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        recent_result = panel.render(expanded=True)
        assert recent_result.border_style == "cyan"

        panel.is_recent = False
        historical_result = panel.render(expanded=True)
        assert historical_result.border_style == "dim"


class TestPanelProperties:
    """Test panel configuration properties."""

    def test_title_align_left(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello")
        result = panel.render()
        assert result.title_align == "left"

    def test_expand_false(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="hello")
        result = panel.render()
        assert result.expand is False


class TestRenderPlain:
    """Test plain text rendering for no-color terminals."""

    def test_render_plain_returns_string(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2\nline3", exit_code=0)
        result = panel.render_plain()
        assert isinstance(result, str)

    def test_render_plain_contains_tool_name(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2\nline3", exit_code=1)
        result = panel.render_plain()
        assert "bash" in result

    def test_render_plain_contains_exit_code(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2\nline3", exit_code=1)
        result = panel.render_plain()
        assert "exit code 1" in result

    def test_render_plain_contains_line_count(self) -> None:
        panel = ResultPanelComponent(tool_name="bash", output="line1\nline2\nline3", exit_code=0)
        result = panel.render_plain()
        assert "3 lines" in result

    def test_render_plain_format(self) -> None:
        panel = ResultPanelComponent(tool_name="grep", output="match1\nmatch2", exit_code=0)
        result = panel.render_plain()
        assert result == "  grep -> exit code 0, 2 lines"


class TestImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import ResultPanelComponent as Imported

        assert Imported is ResultPanelComponent
