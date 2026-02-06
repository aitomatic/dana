"""Result panel component for displaying tool results with collapse/expand."""

from rich.panel import Panel
from rich.text import Text


class ResultPanelComponent:
    """Renders a tool result as a collapsible Rich Panel.

    Recent results have visible borders and can be expanded/collapsed.
    Historical results are dimmed with no border.
    """

    def __init__(
        self,
        tool_name: str,
        output: str,
        exit_code: int = 0,
        is_recent: bool = True,
    ) -> None:
        self.tool_name = tool_name
        self.output = output
        self.exit_code = exit_code
        self.is_recent = is_recent
        self._line_count = len(output.split("\n")) if output else 0

    @property
    def line_count(self) -> int:
        """Number of lines in the output."""
        return self._line_count

    @property
    def default_expanded(self) -> bool:
        """Whether this panel should be expanded by default (<10 lines)."""
        return self._line_count < 10

    def render(self, expanded: bool | None = None, selected: bool = False) -> Panel:
        """Render the result panel.

        Args:
            expanded: Override expand state. If None, uses default_expanded.
            selected: Whether this panel is currently selected (keyboard nav highlight).

        Returns:
            A Rich Panel - collapsed shows summary, expanded shows full output.
        """
        if expanded is None:
            expanded = self.default_expanded

        if expanded:
            body: Text | str = Text(self.output) if self.output else Text("")
        else:
            body = self._collapsed_summary()

        if selected and self.is_recent:
            border_style = "bold yellow"
        elif self.is_recent:
            border_style = "cyan"
        else:
            border_style = "dim"

        return Panel(
            body,
            title=self.tool_name,
            title_align="left",
            border_style=border_style,
            expand=False,
        )

    def _collapsed_summary(self) -> Text:
        """Generate collapsed summary text.

        Format: 'tool_name -> exit code N, M lines'
        """
        return Text(
            f"{self.tool_name} -> exit code {self.exit_code}, {self._line_count} lines",
            style="dim",
        )
