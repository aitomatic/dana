"""
Task management and cancellation for Dana TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskInfo:
    """Information about a running task."""

    task: asyncio.Task
    agent_name: str
    start_time: float = field(default_factory=time.perf_counter)
    description: str = ""

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.perf_counter() - self.start_time

    @property
    def is_running(self) -> bool:
        """Check if task is still running."""
        return not self.task.done()


class CancelToken:
    """Cancellation token for graceful task termination."""

    def __init__(self):
        self._cancelled = False
        self._callbacks: list[Callable[[], None]] = []

    def cancel(self) -> None:
        """Cancel the token and notify callbacks."""
        if not self._cancelled:
            self._cancelled = True
            for callback in self._callbacks:
                try:
                    callback()
                except Exception:
                    pass  # Ignore callback errors

    def is_cancelled(self) -> bool:
        """Check if the token is cancelled."""
        return self._cancelled

    def add_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when cancelled."""
        if self._cancelled:
            callback()  # Call immediately if already cancelled
        else:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove a callback."""
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass


class TaskManager:
    """Manages agent tasks with cancellation support."""

    def __init__(self):
        self._tasks: dict[str, TaskInfo] = {}  # task_id -> TaskInfo
        self._agent_tasks: dict[str, set[str]] = {}  # agent_name -> set of task_ids
        self._cancel_tokens: dict[str, CancelToken] = {}  # task_id -> CancelToken
        self._next_task_id = 1

    def start_task(self, agent_name: str, coro: Any, description: str = "") -> tuple[str, CancelToken]:
        """Start a new task for an agent.

        Args:
            agent_name: Name of the agent
            coro: Coroutine to run
            description: Optional task description

        Returns:
            Tuple of (task_id, cancel_token)
        """
        task_id = f"task_{self._next_task_id}"
        self._next_task_id += 1

        # Create cancel token
        cancel_token = CancelToken()
        self._cancel_tokens[task_id] = cancel_token

        # Create and start task
        task = asyncio.create_task(coro)
        task_info = TaskInfo(task=task, agent_name=agent_name, description=description)

        self._tasks[task_id] = task_info

        # Track agent's tasks
        if agent_name not in self._agent_tasks:
            self._agent_tasks[agent_name] = set()
        self._agent_tasks[agent_name].add(task_id)

        # Auto-cleanup when task completes
        task.add_done_callback(lambda _: self._cleanup_task(task_id))

        return task_id, cancel_token

    def cancel_task(self, task_id: str, timeout: float = 0.15) -> bool:
        """Cancel a specific task.

        Args:
            task_id: ID of the task to cancel
            timeout: Maximum time to wait for cancellation

        Returns:
            True if cancelled successfully
        """
        if task_id not in self._tasks:
            return False

        task_info = self._tasks[task_id]
        cancel_token = self._cancel_tokens.get(task_id)

        # Signal cancellation through token
        if cancel_token:
            cancel_token.cancel()

        # Cancel the asyncio task
        if not task_info.task.done():
            task_info.task.cancel()

        return True

    def cancel_agent_tasks(self, agent_name: str, timeout: float = 0.15) -> int:
        """Cancel all tasks for a specific agent.

        Args:
            agent_name: Name of the agent
            timeout: Maximum time to wait for cancellation

        Returns:
            Number of tasks cancelled
        """
        if agent_name not in self._agent_tasks:
            return 0

        task_ids = self._agent_tasks[agent_name].copy()
        cancelled_count = 0

        for task_id in task_ids:
            if self.cancel_task(task_id, timeout):
                cancelled_count += 1

        return cancelled_count

    def cancel_all_tasks(self, timeout: float = 0.15) -> int:
        """Cancel all running tasks.

        Args:
            timeout: Maximum time to wait for cancellation

        Returns:
            Number of tasks cancelled
        """
        task_ids = list(self._tasks.keys())
        cancelled_count = 0

        for task_id in task_ids:
            if self.cancel_task(task_id, timeout):
                cancelled_count += 1

        return cancelled_count

    def get_agent_tasks(self, agent_name: str) -> list[TaskInfo]:
        """Get all tasks for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of TaskInfo objects
        """
        if agent_name not in self._agent_tasks:
            return []

        return [self._tasks[task_id] for task_id in self._agent_tasks[agent_name] if task_id in self._tasks]

    def get_running_agents(self) -> list[str]:
        """Get list of agents with running tasks."""
        running_agents = []
        for agent_name, task_ids in self._agent_tasks.items():
            if any(task_id in self._tasks and self._tasks[task_id].is_running for task_id in task_ids):
                running_agents.append(agent_name)
        return running_agents

    def is_agent_running(self, agent_name: str) -> bool:
        """Check if an agent has any running tasks."""
        return agent_name in self.get_running_agents()

    def get_task_count(self) -> int:
        """Get total number of running tasks."""
        return len([task_info for task_info in self._tasks.values() if task_info.is_running])

    def get_task_info(self, task_id: str) -> TaskInfo | None:
        """Get information about a specific task."""
        return self._tasks.get(task_id)

    def _cleanup_task(self, task_id: str) -> None:
        """Clean up completed or cancelled task."""
        if task_id not in self._tasks:
            return

        task_info = self._tasks[task_id]
        agent_name = task_info.agent_name

        # Remove from tracking
        del self._tasks[task_id]

        if task_id in self._cancel_tokens:
            del self._cancel_tokens[task_id]

        if agent_name in self._agent_tasks:
            self._agent_tasks[agent_name].discard(task_id)
            # Clean up empty agent entry
            if not self._agent_tasks[agent_name]:
                del self._agent_tasks[agent_name]

    def get_stats(self) -> dict:
        """Get task manager statistics."""
        running_tasks = [t for t in self._tasks.values() if t.is_running]

        return {
            "total_tasks": len(self._tasks),
            "running_tasks": len(running_tasks),
            "agents_with_tasks": len(self._agent_tasks),
            "avg_task_duration": (sum(t.elapsed for t in running_tasks) / len(running_tasks) if running_tasks else 0.0),
        }


# Global task manager instance
task_manager = TaskManager()
