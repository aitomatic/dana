"""
Todo Resource - Progress tracking for Dana agents.

Provides the todo_write() tool mirroring Claude Code's TodoWrite signature.
Tracks task progress with pending, in_progress, and completed states.
"""

from __future__ import annotations

from typing import Any

import structlog

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


logger = structlog.get_logger()


class ToDoResource(BaseResource):
    """Resource for tracking task progress.

    Provides a todo list that agents can use to:
    - Plan and track multi-step tasks
    - Give users visibility into progress
    - Organize complex work into manageable items

    Todo items have three states:
    - pending: Task not yet started
    - in_progress: Currently working on
    - completed: Task finished successfully

    Usage:
        resource = ToDoResource()
        agent.with_resources(resource)

        # Agent calls:
        result = await resource.todo_write([
            {"content": "Read config", "status": "completed", "activeForm": "Reading config"},
            {"content": "Run tests", "status": "in_progress", "activeForm": "Running tests"},
            {"content": "Deploy", "status": "pending", "activeForm": "Deploying"},
        ])
    """

    def __init__(self, resource_id: str = "todo", **kwargs: Any):
        """Initialize the ToDoResource.

        Args:
            resource_id: Unique identifier for this resource (default: "todo")
            **kwargs: Additional arguments passed to BaseResource.
        """
        super().__init__(resource_type="todo", resource_id=resource_id, **kwargs)
        self._todos: list[dict] = []

    @tool_use
    async def todo_write(self, todos: list[dict]) -> dict[str, Any]:
        """Create or update the task list.

        Args:
            todos: Array of todo items, each with:
                - content (str): Task description in imperative form
                    Example: "Run the build", "Fix type errors"
                - status (str): "pending", "in_progress", or "completed"
                - activeForm (str): Present continuous form for display
                    Example: "Running the build", "Fixing type errors"

        Returns:
            Dict with:
            - success: Whether the update succeeded
            - message: Human-readable status message
            - summary: Progress summary (completed/total)
            - todos: The current todo list
        """
        valid_statuses = {"pending", "in_progress", "completed"}

        # Validate todos
        for i, todo in enumerate(todos):
            if "content" not in todo:
                return {
                    "success": False,
                    "message": f"Todo item {i} missing 'content' field",
                    "summary": None,
                    "todos": self._todos,
                }
            if "status" not in todo:
                return {
                    "success": False,
                    "message": f"Todo item {i} missing 'status' field",
                    "summary": None,
                    "todos": self._todos,
                }
            if "activeForm" not in todo:
                return {
                    "success": False,
                    "message": f"Todo item {i} missing 'activeForm' field",
                    "summary": None,
                    "todos": self._todos,
                }
            if todo["status"] not in valid_statuses:
                return {
                    "success": False,
                    "message": f"Todo item {i} has invalid status '{todo['status']}'",
                    "summary": None,
                    "todos": self._todos,
                }

        # Store todos
        self._todos = todos

        # Calculate summary
        pending = sum(1 for t in todos if t["status"] == "pending")
        in_progress = sum(1 for t in todos if t["status"] == "in_progress")
        completed = sum(1 for t in todos if t["status"] == "completed")
        total = len(todos)

        summary = f"{completed}/{total} completed, {in_progress} in progress, {pending} pending"

        logger.info(
            "Todo list updated",
            total=total,
            completed=completed,
            in_progress=in_progress,
            pending=pending,
        )

        return {
            "success": True,
            "message": "Todo list updated successfully",
            "summary": summary,
            "todos": self._todos,
        }

    def get_todos(self) -> list[dict]:
        """Get the current todo list.

        Returns:
            Copy of the current todo list
        """
        return self._todos.copy()

    def get_in_progress(self) -> list[dict]:
        """Get todos currently in progress.

        Returns:
            List of in-progress todo items
        """
        return [t for t in self._todos if t["status"] == "in_progress"]

    def get_completed(self) -> list[dict]:
        """Get completed todos.

        Returns:
            List of completed todo items
        """
        return [t for t in self._todos if t["status"] == "completed"]

    def get_pending(self) -> list[dict]:
        """Get pending todos.

        Returns:
            List of pending todo items
        """
        return [t for t in self._todos if t["status"] == "pending"]

    def format_for_display(self) -> str:
        """Format todo list for human-readable display.

        Returns:
            Formatted string with status indicators
        """
        if not self._todos:
            return "No tasks in todo list."

        status_icons = {
            "pending": "[ ]",
            "in_progress": "[>]",
            "completed": "[x]",
        }

        lines = []
        for todo in self._todos:
            icon = status_icons.get(todo["status"], "[?]")
            status = todo["status"]

            if status == "in_progress":
                lines.append(f"{icon} {todo['activeForm']}")
            else:
                lines.append(f"{icon} {todo['content']}")

        # Add summary
        pending = sum(1 for t in self._todos if t["status"] == "pending")
        in_progress = sum(1 for t in self._todos if t["status"] == "in_progress")
        completed = sum(1 for t in self._todos if t["status"] == "completed")
        total = len(self._todos)

        lines.append("")
        lines.append(f"Progress: {completed}/{total} completed, {in_progress} in progress, {pending} pending")

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear the todo list."""
        self._todos = []
