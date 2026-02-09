"""Progress tracker component for displaying todo item progress."""

from typing import Any

from rich.table import Table
from rich.text import Text


# Status icons for todo items
_STATUS_ICONS = {
    "completed": "\u2714",  # ✔ checkmark
    "in_progress": "\u25cf",  # ● filled circle (spinner substitute for static render)
    "pending": "\u25cb",  # ○ open circle
}

_STATUS_STYLES = {
    "completed": "green",
    "in_progress": "yellow",
    "pending": "dim",
}


class ProgressTrackerComponent:
    """Displays progress for multi-step tasks (todo items).

    Renders a compact table with status icons and a progress summary
    showing completed/total counts and the current task description.
    """

    def __init__(self) -> None:
        self._todos: list[dict[str, Any]] = []

    @property
    def todos(self) -> list[dict[str, Any]]:
        """Current todo items."""
        return self._todos

    @property
    def completed_count(self) -> int:
        """Number of completed items."""
        return sum(1 for t in self._todos if t.get("status") == "completed")

    @property
    def total_count(self) -> int:
        """Total number of items."""
        return len(self._todos)

    @property
    def current_task(self) -> str:
        """Description of the current in-progress task, or empty string."""
        for todo in self._todos:
            if todo.get("status") == "in_progress":
                return str(todo.get("content", ""))
        return ""

    def update_todos(self, todo_items: list[dict[str, Any]]) -> None:
        """Update the internal todo list.

        Args:
            todo_items: List of todo dicts with 'content' and 'status' keys.
                Status values: 'completed', 'in_progress', 'pending'.
        """
        self._todos = list(todo_items)

    def render(self) -> Table | None:
        """Render progress as a rich Table.

        Returns:
            A rich Table showing todo items with status icons,
            or None if there are no todo items.
        """
        if not self._todos:
            return None

        table = Table(
            show_header=False,
            show_edge=False,
            box=None,
            padding=(0, 1),
            expand=False,
        )
        table.add_column("icon", width=2, no_wrap=True)
        table.add_column("task")

        for todo in self._todos:
            status = todo.get("status", "pending")
            content = str(todo.get("content", ""))
            icon = _STATUS_ICONS.get(status, _STATUS_ICONS["pending"])
            style = _STATUS_STYLES.get(status, "dim")
            table.add_row(
                Text(icon, style=style),
                Text(content, style=style),
            )

        return table

    def render_summary(self) -> str:
        """Render a compact progress summary line.

        Format: '[N/M] Current task description'

        Returns:
            Progress summary string, or empty string if no todos.
        """
        if not self._todos:
            return ""

        completed = self.completed_count
        total = self.total_count
        current = self.current_task

        if current:
            return f"[{completed}/{total}] {current}"
        return f"[{completed}/{total}]"
