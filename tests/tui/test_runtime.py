"""
Standalone unit tests for Dana TUI runtime sandbox.

This version doesn't import the full TUI package to avoid textual dependency.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path

import pytest

# Add the project root to path so we can import dana.apps.tui.core
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dana.apps.tui.core.events import Done, Status, Token
from dana.builtin_types.agent import AgentInstance, AgentType
from dana.core.lang.dana_sandbox import DanaSandbox


class MockTestAgent(AgentInstance):
    """Mock agent for testing."""

    def __init__(self, name: str, response_text: str = "test response"):
        # Create a simple agent type for testing with all needed fields
        agent_type = AgentType(
            name=f"{name}_type",
            fields={"name": "str", "response_text": "str", "chat_calls": "list"},
            field_order=["name", "response_text", "chat_calls"],
            field_defaults={"name": name, "response_text": response_text, "chat_calls": []},
        )
        super().__init__(agent_type, {"name": name, "response_text": response_text, "chat_calls": []})

    async def chat(self, message: str):
        """Mock chat implementation."""
        self.chat_calls.append(message)
        yield Status("thinking", f"Processing: {message}")
        for char in self.response_text:
            yield Token(char)
        yield Done()


class TestAgent:
    """Test the Agent base class."""

    def test_initial_state(self):
        """Test agent initial state."""
        agent = MockTestAgent("test_agent")
        assert agent.name == "test_agent"

        metrics = agent.get_metrics()
        assert metrics["tokens_per_sec"] == 0.0
        assert metrics["elapsed_time"] == 0.0
        assert metrics["current_step"] == "idle"
        assert metrics["is_running"] is False

    def test_update_metric(self):
        """Test metric updates."""
        agent = MockTestAgent("test_agent")

        agent.update_metric("is_running", True)
        agent.update_metric("current_step", "processing")
        agent.update_metric("tokens_per_sec", 15.5)

        metrics = agent.get_metrics()
        assert metrics["is_running"] is True
        assert metrics["current_step"] == "processing"
        assert metrics["tokens_per_sec"] == 15.5

    def test_invalid_metric_update(self):
        """Test that invalid metric keys are ignored."""
        agent = MockTestAgent("test_agent")

        # This should not crash or add new keys
        agent.update_metric("invalid_key", "value")

        metrics = agent.get_metrics()
        assert "invalid_key" not in metrics

    @pytest.mark.asyncio
    async def test_chat_functionality(self):
        """Test agent chat functionality."""
        agent = MockTestAgent("test_agent", "hello world")

        events = []
        async for event in agent.chat("test message"):
            events.append(event)

        # Check that we got the expected events
        assert len(events) >= 3  # Status + Tokens + Done
        assert isinstance(events[0], Status)
        assert isinstance(events[-1], Done)

        # Check that token events spell out the response
        token_chars = [event.text for event in events if isinstance(event, Token)]
        assert "".join(token_chars) == "hello world"

        # Check that chat was recorded
        assert agent.chat_calls == ["test message"]


class TestDanaSandbox:
    """Test the DanaSandbox functionality."""

    @pytest.fixture
    def sandbox(self):
        """Create a fresh sandbox for each test."""
        return DanaSandbox()

    def test_initialization(self, sandbox):
        """Test sandbox initializes properly."""
        assert sandbox is not None
        assert sandbox._context is not None
        # Core DanaSandbox doesn't need wrapper methods

    def test_execute_simple_expression(self, sandbox):
        """Test executing simple Dana expressions."""
        result = sandbox.execute_string("5 + 3")
        assert result.success is True
        assert result.result == 8

    def test_execute_variable_assignment(self, sandbox):
        """Test executing variable assignments."""
        result = sandbox.execute_string("x = 10")
        assert result.success is True

        # Variable should be available in subsequent executions
        result = sandbox.execute_string("x * 2")
        assert result.success is True
        assert result.result == 20

    def test_execute_invalid_syntax(self, sandbox):
        """Test executing invalid Dana code."""
        result = sandbox.execute_string("5 +")  # Incomplete expression
        assert result.success is False
        assert result.error is not None

    def test_execute_string_operations(self, sandbox):
        """Test executing string operations."""
        result = sandbox.execute_string('"hello" + " world"')
        assert result.success is True
        assert result.result == "hello world"

    def test_get_dana_context(self, sandbox):
        """Test getting the Dana context."""
        context = sandbox._context
        assert context is not None

        # Execute something to modify context
        sandbox.execute_string("test_var = 42")

        # Context should contain the variable in local scope
        updated_context = sandbox._context
        assert "test_var" in updated_context._state["local"]

    def test_get_dana_sandbox_access(self, sandbox):
        """Test getting access to underlying Dana sandbox."""
        # Core DanaSandbox is already the main sandbox, no wrapper needed
        assert sandbox is not None

        # Should be a CoreDanaSandbox instance
        from dana.core.lang.dana_sandbox import DanaSandbox as CoreDanaSandbox

        assert isinstance(sandbox, CoreDanaSandbox)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
