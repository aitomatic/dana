"""Tests for ProgressTrackerComponent todo progress display."""

from typing import Any

from rich.table import Table
from rich.text import Text

from dana.cli.components.progress_tracker import (
    _STATUS_ICONS,
    ProgressTrackerComponent,
)


def _get_cell(table: Table, row: int, col: int) -> Any:
    """Get a cell value from a rich Table by row and column index.

    Rich stores cells in columns, not rows: table.columns[col]._cells[row].
    """
    return table.columns[col]._cells[row]


class TestProgressTrackerInit:
    """Test constructor and defaults."""

    def test_default_empty_todos(self) -> None:
        tracker = ProgressTrackerComponent()
        assert tracker.todos == []

    def test_default_counts(self) -> None:
        tracker = ProgressTrackerComponent()
        assert tracker.completed_count == 0
        assert tracker.total_count == 0

    def test_default_current_task_empty(self) -> None:
        tracker = ProgressTrackerComponent()
        assert tracker.current_task == ""


class TestUpdateTodos:
    """Test update_todos method."""

    def test_update_with_items(self) -> None:
        tracker = ProgressTrackerComponent()
        items = [
            {"content": "Task 1", "status": "completed"},
            {"content": "Task 2", "status": "in_progress"},
        ]
        tracker.update_todos(items)
        assert len(tracker.todos) == 2

    def test_update_replaces_previous(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Old", "status": "pending"}])
        tracker.update_todos([{"content": "New", "status": "completed"}])
        assert len(tracker.todos) == 1
        assert tracker.todos[0]["content"] == "New"

    def test_update_with_empty_list(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Task", "status": "pending"}])
        tracker.update_todos([])
        assert tracker.todos == []

    def test_update_copies_list(self) -> None:
        """Modifying original list doesn't affect tracker."""
        tracker = ProgressTrackerComponent()
        items: list[dict[str, str]] = [{"content": "Task", "status": "pending"}]
        tracker.update_todos(items)
        items.append({"content": "Extra", "status": "pending"})
        assert len(tracker.todos) == 1


class TestCompletedCount:
    """Test completed_count property."""

    def test_no_completed(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "pending"},
                {"content": "B", "status": "in_progress"},
            ]
        )
        assert tracker.completed_count == 0

    def test_some_completed(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "in_progress"},
                {"content": "C", "status": "pending"},
            ]
        )
        assert tracker.completed_count == 1

    def test_all_completed(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "completed"},
            ]
        )
        assert tracker.completed_count == 2

    def test_total_count(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "in_progress"},
                {"content": "C", "status": "pending"},
            ]
        )
        assert tracker.total_count == 3


class TestCurrentTask:
    """Test current_task property."""

    def test_returns_in_progress_task(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "Done task", "status": "completed"},
                {"content": "Active task", "status": "in_progress"},
                {"content": "Future task", "status": "pending"},
            ]
        )
        assert tracker.current_task == "Active task"

    def test_returns_first_in_progress(self) -> None:
        """If multiple in_progress, returns the first one."""
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "First active", "status": "in_progress"},
                {"content": "Second active", "status": "in_progress"},
            ]
        )
        assert tracker.current_task == "First active"

    def test_no_in_progress_returns_empty(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "Done", "status": "completed"},
                {"content": "Pending", "status": "pending"},
            ]
        )
        assert tracker.current_task == ""

    def test_empty_todos_returns_empty(self) -> None:
        tracker = ProgressTrackerComponent()
        assert tracker.current_task == ""


class TestRender:
    """Test render method returns Table or None."""

    def test_empty_todos_returns_none(self) -> None:
        tracker = ProgressTrackerComponent()
        assert tracker.render() is None

    def test_returns_table_with_items(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Task 1", "status": "pending"}])
        result = tracker.render()
        assert isinstance(result, Table)

    def test_table_has_correct_row_count(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "in_progress"},
                {"content": "C", "status": "pending"},
            ]
        )
        result = tracker.render()
        assert result is not None
        assert result.row_count == 3

    def test_completed_item_has_checkmark(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Done", "status": "completed"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert isinstance(icon_cell, Text)
        assert str(icon_cell) == _STATUS_ICONS["completed"]

    def test_in_progress_item_has_spinner_icon(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Active", "status": "in_progress"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert isinstance(icon_cell, Text)
        assert str(icon_cell) == _STATUS_ICONS["in_progress"]

    def test_pending_item_has_circle(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Todo", "status": "pending"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert isinstance(icon_cell, Text)
        assert str(icon_cell) == _STATUS_ICONS["pending"]

    def test_task_content_in_table(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "My task description", "status": "pending"}])
        result = tracker.render()
        assert result is not None
        task_cell = _get_cell(result, 0, 1)
        assert isinstance(task_cell, Text)
        assert str(task_cell) == "My task description"

    def test_unknown_status_defaults_to_pending_icon(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Unknown", "status": "weird"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert str(icon_cell) == _STATUS_ICONS["pending"]

    def test_missing_content_renders_empty(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"status": "pending"}])
        result = tracker.render()
        assert result is not None
        task_cell = _get_cell(result, 0, 1)
        assert str(task_cell) == ""

    def test_render_after_clear_returns_none(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Task", "status": "pending"}])
        assert tracker.render() is not None
        tracker.update_todos([])
        assert tracker.render() is None


class TestRenderSummary:
    """Test render_summary method."""

    def test_empty_returns_empty_string(self) -> None:
        tracker = ProgressTrackerComponent()
        assert tracker.render_summary() == ""

    def test_with_in_progress_task(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "Done", "status": "completed"},
                {"content": "Working on it", "status": "in_progress"},
                {"content": "Later", "status": "pending"},
            ]
        )
        assert tracker.render_summary() == "[1/3] Working on it"

    def test_all_completed(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "completed"},
            ]
        )
        assert tracker.render_summary() == "[2/2]"

    def test_none_completed(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "First task", "status": "in_progress"},
                {"content": "Second task", "status": "pending"},
            ]
        )
        assert tracker.render_summary() == "[0/2] First task"

    def test_no_in_progress_shows_count_only(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos(
            [
                {"content": "A", "status": "completed"},
                {"content": "B", "status": "pending"},
            ]
        )
        assert tracker.render_summary() == "[1/2]"


class TestProgressTrackerStyles:
    """Test visual styling of rendered items."""

    def test_completed_has_green_style(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Done", "status": "completed"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert isinstance(icon_cell, Text)
        assert icon_cell.style == "green"

    def test_in_progress_has_yellow_style(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Active", "status": "in_progress"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert isinstance(icon_cell, Text)
        assert icon_cell.style == "yellow"

    def test_pending_has_dim_style(self) -> None:
        tracker = ProgressTrackerComponent()
        tracker.update_todos([{"content": "Later", "status": "pending"}])
        result = tracker.render()
        assert result is not None
        icon_cell = _get_cell(result, 0, 0)
        assert isinstance(icon_cell, Text)
        assert icon_cell.style == "dim"


class TestProgressTrackerImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import ProgressTrackerComponent as Imported

        assert Imported is ProgressTrackerComponent
