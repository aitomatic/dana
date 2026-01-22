"""Resource for tracking task progress.

Provides todo_write() tool mirroring Claude Code's TodoWrite signature.
"""

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class ToDoResource(BaseResource):
    """Resource for tracking task progress."""

    def __init__(self, resource_id: str, **kwargs):
        """Initialize the ProgressResource.

        Args:
            resource_id: Unique identifier for this resource instance.
            **kwargs: Additional arguments passed to the base resource.
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self._todos: list[dict] = []

    @tool_use
    async def todo_write(self, todos: list[dict]) -> str:
        """Create and manage a task list for tracking extraction progress.

        Args:
            todos: Array of todo items, each with:
                - content (str): Task description in imperative form (e.g., "Extract HVAC equipment")
                - status (str): "pending", "in_progress", or "completed"
                - activeForm (str): Present continuous form (e.g., "Extracting HVAC equipment")

        Returns:
            Formatted todo list with status indicators.
        """
        # Validate todos
        valid_statuses = {"pending", "in_progress", "completed"}

        for i, todo in enumerate(todos):
            if "content" not in todo:
                return f"Error: Todo item {i} missing 'content' field"
            if "status" not in todo:
                return f"Error: Todo item {i} missing 'status' field"
            if "activeForm" not in todo:
                return f"Error: Todo item {i} missing 'activeForm' field"
            if todo["status"] not in valid_statuses:
                return f"Error: Todo item {i} has invalid status '{todo['status']}'"

        # Store todos
        self._todos = todos

        # Format output
        status_icons = {"pending": "○", "in_progress": "◐", "completed": "●"}

        output_lines = ["Todo List:"]
        output_lines.append("-" * 40)

        for todo in todos:
            icon = status_icons.get(todo["status"], "?")
            status = todo["status"]
            content = todo["content"]

            if status == "in_progress":
                output_lines.append(f"  {icon} [{status:11}] {todo['activeForm']}")
            else:
                output_lines.append(f"  {icon} [{status:11}] {content}")

        output_lines.append("-" * 40)

        # Summary
        pending = sum(1 for t in todos if t["status"] == "pending")
        in_progress = sum(1 for t in todos if t["status"] == "in_progress")
        completed = sum(1 for t in todos if t["status"] == "completed")
        total = len(todos)

        output_lines.append(f"Progress: {completed}/{total} completed, {in_progress} in progress, {pending} pending")

        return "\n".join(output_lines)

    def get_todos(self) -> list[dict]:
        """Get current todo list.

        Returns:
            List of todo items.
        """
        return self._todos.copy()

    def get_in_progress(self) -> list[dict]:
        """Get todos currently in progress.

        Returns:
            List of in-progress todo items.
        """
        return [t for t in self._todos if t["status"] == "in_progress"]

    def get_completed(self) -> list[dict]:
        """Get completed todos.

        Returns:
            List of completed todo items.
        """
        return [t for t in self._todos if t["status"] == "completed"]
