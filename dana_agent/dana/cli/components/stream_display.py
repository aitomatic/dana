"""Streaming text display component for real-time LLM response rendering."""

from rich.text import Text


class StreamDisplayComponent:
    """Displays streaming LLM response text with line limiting.

    Accumulates text chunks and renders them as rich Text.
    Long responses are truncated to show only the last N lines
    with an indicator of hidden lines above.
    """

    def __init__(self, max_visible_lines: int = 20, line_threshold: int = 50) -> None:
        self._buffer = ""
        self._max_visible_lines = max_visible_lines
        self._line_threshold = line_threshold

    @property
    def buffer(self) -> str:
        """The full accumulated text buffer."""
        return self._buffer

    @property
    def line_count(self) -> int:
        """Number of lines in the buffer."""
        if not self._buffer:
            return 0
        return self._buffer.count("\n") + 1

    def append_chunk(self, text: str) -> None:
        """Append a text chunk to the buffer.

        Args:
            text: The text chunk to append.
        """
        self._buffer += text

    def clear(self) -> None:
        """Reset the buffer for a new response."""
        self._buffer = ""

    def render(self) -> Text:
        """Render the buffer as a Rich Text object.

        If the buffer exceeds the line threshold, only the last
        max_visible_lines are shown with a '[N lines above]' indicator.

        Returns:
            A Rich Text object with the display content.
        """
        if not self._buffer:
            return Text("")

        lines = self._buffer.split("\n")
        total_lines = len(lines)

        if total_lines > self._line_threshold:
            hidden = total_lines - self._max_visible_lines
            visible_lines = lines[-self._max_visible_lines :]
            header = f"[{hidden} lines above]"
            display_text = header + "\n" + "\n".join(visible_lines)
            return Text(display_text)

        return Text(self._buffer)
