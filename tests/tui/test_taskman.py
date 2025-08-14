"""
Standalone unit tests for Dana TUI task manager.

This version doesn't import the full TUI package to avoid textual dependency.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add the project root to path so we can import dana.tui.core
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dana.tui.core.taskman import task_manager


class TestTaskManager:
    """Test the task manager functionality."""

    def test_task_manager_initial_state(self):
        """Test task manager initial state."""
        assert task_manager is not None
        assert hasattr(task_manager, "_tasks")
        assert hasattr(task_manager, "start_task")
        assert hasattr(task_manager, "get_task_info")
        assert hasattr(task_manager, "cancel_task")

    @pytest.mark.asyncio
    async def test_add_and_get_task(self):
        """Test adding and retrieving tasks."""
        # Clear any existing tasks
        task_manager._tasks.clear()

        # Add task using the proper method
        async def dummy_coro():
            await asyncio.sleep(0.01)
            return "done"

        task_id, cancel_token = task_manager.start_task("test_agent", dummy_coro(), "test task")

        # Verify task was added
        retrieved_task = task_manager.get_task_info(task_id)
        assert retrieved_task is not None
        assert retrieved_task.agent_name == "test_agent"

        # Test getting non-existent task
        assert task_manager.get_task_info("non_existent") is None

        # Clean up
        task_manager.cancel_task(task_id)

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """Test listing tasks."""
        # Clear any existing tasks
        task_manager._tasks.clear()

        # Add some tasks
        async def dummy_coro1():
            await asyncio.sleep(0.01)
            return "done1"

        async def dummy_coro2():
            await asyncio.sleep(0.01)
            return "done2"

        task_id1, _ = task_manager.start_task("agent_1", dummy_coro1(), "task 1")
        task_id2, _ = task_manager.start_task("agent_2", dummy_coro2(), "task 2")

        # Get task info
        task1 = task_manager.get_task_info(task_id1)
        task2 = task_manager.get_task_info(task_id2)

        assert task1 is not None
        assert task2 is not None
        assert task1.agent_name == "agent_1"
        assert task2.agent_name == "agent_2"

        # Clean up
        task_manager.cancel_task(task_id1)
        task_manager.cancel_task(task_id2)

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test task cancellation."""
        # Clear any existing tasks
        task_manager._tasks.clear()

        # Start a task
        async def long_task():
            await asyncio.sleep(1.0)
            return "done"

        task_id, cancel_token = task_manager.start_task("test_agent", long_task(), "long task")

        # Cancel the task
        cancelled = task_manager.cancel_task(task_id)
        assert cancelled is True

        # Wait a bit for cleanup
        await asyncio.sleep(0.1)

        # Verify task is cancelled and cleaned up
        task = task_manager.get_task_info(task_id)
        assert task is None

    @pytest.mark.asyncio
    async def test_multiple_concurrent_tasks(self):
        """Test multiple concurrent tasks."""
        # Clear any existing tasks
        task_manager._tasks.clear()

        # Start multiple tasks using regular coroutines
        task_ids = []
        for i in range(3):

            async def dummy_coro(task_num=i):
                # Add a delay to keep the task running
                await asyncio.sleep(0.1)
                return f"task {task_num} done"

            task_id, _ = task_manager.start_task(f"agent_{i}", dummy_coro(), f"task for agent_{i}")
            task_ids.append(task_id)

        # Wait a bit for tasks to start
        await asyncio.sleep(0.05)

        # Verify all tasks are running
        for task_id in task_ids:
            task_info = task_manager.get_task_info(task_id)
            assert task_info is not None, f"Task {task_id} not found"

        # Cancel all tasks
        for task_id in task_ids:
            task_manager.cancel_task(task_id)

        # Wait a bit for tasks to be cleaned up
        await asyncio.sleep(0.1)

        # Verify all tasks are cancelled and cleaned up
        for task_id in task_ids:
            task_info = task_manager.get_task_info(task_id)
            assert task_info is None
