"""
Standalone unit tests for Dana TUI task manager.

This version doesn't import the full TUI package to avoid textual dependency.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to path so we can import dana.tui.core
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dana.tui.core.events import Done, Status, Token
from dana.tui.core.runtime import Agent
from dana.tui.core.taskman import run_agent_task, task_manager


class MockTestAgent(Agent):
    """Mock agent for testing task manager."""

    def __init__(self, name: str, response_text: str = "test response", delay: float = 0.0):
        super().__init__(name)
        self.response_text = response_text
        self.delay = delay
        self.chat_calls = []
        self.start_time = None
        self.end_time = None

    async def chat(self, message: str):
        """Mock chat implementation with optional delay."""
        self.chat_calls.append(message)
        self.start_time = asyncio.get_event_loop().time()

        yield Status("thinking", f"Processing: {message}")

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        for char in self.response_text:
            yield Token(char)
            if self.delay > 0:
                await asyncio.sleep(self.delay / len(self.response_text))

        self.end_time = asyncio.get_event_loop().time()
        yield Done()


class TestTaskManager:
    """Test the task manager functionality."""

    def test_task_manager_initial_state(self):
        """Test task manager initial state."""
        assert task_manager is not None
        assert hasattr(task_manager, "_tasks")
        assert hasattr(task_manager, "start_task")
        assert hasattr(task_manager, "get_task_info")
        assert hasattr(task_manager, "cancel_task")

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

        # Verify task is cancelled
        task = task_manager.get_task_info(task_id)
        assert task is None or task.task.done()

    async def test_run_agent_task_basic(self):
        """Test basic agent task execution."""
        agent = MockTestAgent("test_agent", "hello world")
        events = []

        async for event in run_agent_task(agent, "test message"):
            events.append(event)

        # Verify we got the expected events
        assert len(events) >= 3  # Status + Tokens + Done
        assert isinstance(events[0], Status)
        assert isinstance(events[-1], Done)

        # Verify agent was called
        assert agent.chat_calls == ["test message"]

    async def test_run_agent_task_with_events(self):
        """Test agent task with event collection."""
        agent = MockTestAgent("test_agent", "response text")
        events = []

        async for event in run_agent_task(agent, "test message"):
            events.append(event)

        # Check that we got token events
        token_events = [e for e in events if isinstance(e, Token)]
        assert len(token_events) > 0

        # Check that tokens spell out the response
        response_text = "".join(e.text for e in token_events)
        assert "response" in response_text

    async def test_run_agent_task_error_handling(self):
        """Test error handling in agent tasks."""

        # Create an agent that raises an exception
        class ErrorAgent(MockTestAgent):
            async def chat(self, message: str):
                yield Status("error", "Something went wrong")
                raise ValueError("Test error")

        agent = ErrorAgent("error_agent")
        events = []

        # Should handle the error gracefully
        try:
            async for event in run_agent_task(agent, "test message"):
                events.append(event)
        except Exception:
            pass  # Expected to fail

        # Should have at least the status event
        assert len(events) >= 1
        assert isinstance(events[0], Status)

    async def test_run_agent_task_cancellation(self):
        """Test task cancellation."""
        agent = MockTestAgent("slow_agent", "slow response", delay=0.5)

        # Start the task
        task = asyncio.create_task(run_agent_task(agent, "test message").__anext__())

        # Cancel after a short delay
        await asyncio.sleep(0.1)
        task.cancel()

        # Should handle cancellation gracefully
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

    async def test_task_manager_integration(self):
        """Test task manager integration with agent tasks."""
        agent = MockTestAgent("test_agent", "integration test")

        # Start task through task manager
        async def agent_coro():
            async for event in agent.chat("test message"):
                yield event

        task_id, cancel_token = task_manager.start_task(agent.name, agent_coro(), "integration test")

        # Verify task is running
        task_info = task_manager.get_task_info(task_id)
        assert task_info is not None
        assert task_info.agent_name == agent.name

        # Cancel the task
        cancelled = task_manager.cancel_task(task_id)
        assert cancelled is True

    async def test_multiple_concurrent_tasks(self):
        """Test multiple concurrent tasks."""
        agents = [MockTestAgent(f"agent_{i}", f"response {i}") for i in range(3)]

        # Start multiple tasks
        task_ids = []
        for agent in agents:

            async def agent_coro(agent=agent):
                async for event in agent.chat("test"):
                    yield event

            task_id, _ = task_manager.start_task(agent.name, agent_coro(), f"task for {agent.name}")
            task_ids.append(task_id)

        # Verify all tasks are running
        for task_id in task_ids:
            task_info = task_manager.get_task_info(task_id)
            assert task_info is not None

        # Cancel all tasks
        for task_id in task_ids:
            task_manager.cancel_task(task_id)

        # Verify all tasks are cancelled
        for task_id in task_ids:
            task_info = task_manager.get_task_info(task_id)
            assert task_info is None
