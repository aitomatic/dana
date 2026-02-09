"""Hint bar component showing contextual keyboard shortcut hints."""

from rich.text import Text


class HintBarComponent:
    """Displays contextual keyboard shortcut hints at the bottom of the display.

    Shows different hints depending on the current state:
    - During processing: "esc to interrupt"
    - When results exist: navigation hints
    - Otherwise: empty
    """

    def render(
        self,
        has_results: bool = False,
        is_processing: bool = False,
    ) -> Text | None:
        """Render contextual hints.

        Args:
            has_results: Whether there are result panels to navigate.
            is_processing: Whether the agent is currently processing.

        Returns:
            A Rich Text with hints, or None if no hints to show.
        """
        if is_processing and has_results:
            return Text(
                "esc to interrupt",
                style="dim",
            )
        if is_processing:
            return Text("esc to interrupt", style="dim")
        if has_results:
            return Text("↑/↓ navigate results · enter to expand", style="dim")
        return None
