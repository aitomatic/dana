"""Tests for StreamDisplayComponent streaming text display."""

from rich.text import Text

from dana.cli.components.stream_display import StreamDisplayComponent


class TestInit:
    """Test initialization and defaults."""

    def test_default_buffer_is_empty(self) -> None:
        display = StreamDisplayComponent()
        assert display.buffer == ""

    def test_default_line_count_is_zero(self) -> None:
        display = StreamDisplayComponent()
        assert display.line_count == 0

    def test_custom_max_visible_lines(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=10)
        assert display._max_visible_lines == 10

    def test_custom_line_threshold(self) -> None:
        display = StreamDisplayComponent(line_threshold=30)
        assert display._line_threshold == 30


class TestAppendChunk:
    """Test chunk accumulation."""

    def test_single_chunk(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("Hello")
        assert display.buffer == "Hello"

    def test_multiple_chunks(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("Hello")
        display.append_chunk(" world")
        assert display.buffer == "Hello world"

    def test_chunks_with_newlines(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("line1\n")
        display.append_chunk("line2\n")
        display.append_chunk("line3")
        assert display.buffer == "line1\nline2\nline3"

    def test_empty_chunk(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("")
        assert display.buffer == ""

    def test_line_count_after_chunks(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("line1\nline2\nline3")
        assert display.line_count == 3


class TestClear:
    """Test buffer clearing."""

    def test_clear_resets_buffer(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("Some text")
        display.clear()
        assert display.buffer == ""

    def test_clear_resets_line_count(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("line1\nline2")
        display.clear()
        assert display.line_count == 0

    def test_can_append_after_clear(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("first")
        display.clear()
        display.append_chunk("second")
        assert display.buffer == "second"


class TestRender:
    """Test rendering output."""

    def test_render_returns_text(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("Hello")
        result = display.render()
        assert isinstance(result, Text)

    def test_render_empty_buffer(self) -> None:
        display = StreamDisplayComponent()
        result = display.render()
        assert isinstance(result, Text)
        assert result.plain == ""

    def test_render_short_content(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("Hello world")
        result = display.render()
        assert result.plain == "Hello world"

    def test_render_preserves_newlines(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("line1\nline2\nline3")
        result = display.render()
        assert result.plain == "line1\nline2\nline3"

    def test_render_below_threshold_shows_all(self) -> None:
        display = StreamDisplayComponent(line_threshold=50)
        lines = "\n".join(f"line {i}" for i in range(50))
        display.append_chunk(lines)
        result = display.render()
        assert result.plain == lines

    def test_render_at_threshold_shows_all(self) -> None:
        """50 lines with 49 newlines = exactly 50 lines, not over threshold."""
        display = StreamDisplayComponent(line_threshold=50)
        lines = "\n".join(f"line {i}" for i in range(50))
        display.append_chunk(lines)
        result = display.render()
        # 50 lines exactly at threshold - should show all
        assert result.plain == lines


class TestLineLimiting:
    """Test line limiting for long responses."""

    def test_long_response_shows_indicator(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=20, line_threshold=50)
        lines = "\n".join(f"line {i}" for i in range(60))
        display.append_chunk(lines)
        result = display.render()
        assert "[40 lines above]" in result.plain

    def test_long_response_shows_last_n_lines(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=20, line_threshold=50)
        lines = "\n".join(f"line {i}" for i in range(60))
        display.append_chunk(lines)
        result = display.render()
        # Should contain the last 20 lines
        assert "line 59" in result.plain
        assert "line 40" in result.plain

    def test_long_response_hides_early_lines(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=20, line_threshold=50)
        lines = "\n".join(f"line {i}" for i in range(60))
        display.append_chunk(lines)
        result = display.render()
        # Should not contain early lines
        assert "line 0\n" not in result.plain
        assert "line 10\n" not in result.plain

    def test_indicator_shows_correct_hidden_count(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=5, line_threshold=10)
        lines = "\n".join(f"line {i}" for i in range(15))
        display.append_chunk(lines)
        result = display.render()
        # 15 lines total, showing last 5 = 10 hidden
        assert "[10 lines above]" in result.plain

    def test_custom_threshold_and_visible(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=3, line_threshold=5)
        lines = "\n".join(f"line {i}" for i in range(8))
        display.append_chunk(lines)
        result = display.render()
        # 8 lines, showing last 3 = 5 hidden
        assert "[5 lines above]" in result.plain
        assert "line 7" in result.plain
        assert "line 5" in result.plain

    def test_just_over_threshold(self) -> None:
        display = StreamDisplayComponent(max_visible_lines=20, line_threshold=50)
        lines = "\n".join(f"line {i}" for i in range(51))
        display.append_chunk(lines)
        result = display.render()
        # 51 lines > 50 threshold, showing last 20 = 31 hidden
        assert "[31 lines above]" in result.plain


class TestLineCount:
    """Test line counting."""

    def test_single_line_no_newline(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("hello")
        assert display.line_count == 1

    def test_two_lines(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("hello\nworld")
        assert display.line_count == 2

    def test_trailing_newline(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("hello\n")
        # "hello\n" splits to ["hello", ""] = 2 lines
        assert display.line_count == 2

    def test_multiple_newlines(self) -> None:
        display = StreamDisplayComponent()
        display.append_chunk("a\nb\nc\nd\ne")
        assert display.line_count == 5


class TestImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import StreamDisplayComponent as Imported

        assert Imported is StreamDisplayComponent
