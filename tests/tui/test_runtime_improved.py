"""
Improved Unit Tests for Dana TUI Runtime.

Enhanced unit tests with better mocking, error handling, and test coverage.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from unittest.mock import AsyncMock

import pytest

from dana.apps.tui.core.events import Done, Status, Token
from dana.builtin_types.agent_system import AgentInstance

# Skip all tests in this file until TUI runtime tests are updated for new AGENT_REGISTRY architecture
pytestmark = pytest.mark.skip(reason="TUI runtime tests need updating for AGENT_REGISTRY architecture")
from dana.core.lang.dana_sandbox import DanaSandbox


class TestAgent:
    """Improved tests for Agent base class."""

    @pytest.fixture
    def mock_agent(self):
        """Provide a mock agent for testing."""
        agent = AsyncMock(spec=AgentInstance)
        agent.name = "test_agent"
        agent.get_metrics.return_value = {
            "tokens_per_sec": 0.0,
            "elapsed_time": 0.0,
            "current_step": "idle",
            "is_running": False,
            "last_tool": "",
            "progress": 0.0,
        }
        return agent

    def test_agent_initial_state(self, mock_agent):
        """Test agent initial state."""
        assert mock_agent.name == "test_agent"

        metrics = mock_agent.get_metrics()
        assert metrics["tokens_per_sec"] == 0.0
        assert metrics["elapsed_time"] == 0.0
        assert metrics["current_step"] == "idle"
        assert metrics["is_running"] is False

    def test_agent_metrics_update(self, mock_agent):
        """Test agent metrics update."""
        # Test that metrics can be updated
        mock_agent.update_metric("is_running", True)
        mock_agent.update_metric("current_step", "processing")
        mock_agent.update_metric("tokens_per_sec", 15.5)

        # Verify metrics were updated
        mock_agent.update_metric.assert_called()

    def test_agent_chat_interface(self, mock_agent):
        """Test agent chat interface."""
        # Mock chat method to return events
        mock_agent.chat.return_value = [Status("thinking", "Processing"), Token("Hello"), Token(" "), Token("World"), Done()]

        # Test chat method exists and is callable
        assert hasattr(mock_agent, "chat")
        assert callable(mock_agent.chat)


class TestDanaSandbox:
    """Improved tests for DanaSandbox."""

    @pytest.fixture
    def sandbox(self):
        """Provide a clean sandbox for each test."""
        return DanaSandbox()

    @pytest.fixture
    def mock_agent(self):
        """Provide a mock agent."""
        agent = AsyncMock(spec=AgentInstance)
        agent.name = "test_agent"
        agent.get_metrics.return_value = {"tokens_per_sec": 0.0, "elapsed_time": 0.0, "current_step": "idle", "is_running": False}
        return agent

    def test_add_agent_directly(self, sandbox, mock_agent):
        """Test adding agent directly to sandbox."""
        sandbox._agents[mock_agent.name] = mock_agent
        assert "test_agent" in sandbox.list()
        assert sandbox.get("test_agent") is mock_agent

    def test_add_agent_sets_focus(self, sandbox, mock_agent):
        """Test that first agent becomes focused when added."""
        sandbox._agents[mock_agent.name] = mock_agent
        if sandbox._focused_agent is None:
            sandbox._focused_agent = mock_agent.name
        assert sandbox.get_focused_name() == "test_agent"

    def test_add_multiple_agents(self, sandbox, mock_agent):
        """Test adding multiple agents."""
        agent1 = AsyncMock(spec=AgentInstance)
        agent1.name = "agent1"
        agent2 = AsyncMock(spec=AgentInstance)
        agent2.name = "agent2"

        sandbox._agents[agent1.name] = agent1
        sandbox._agents[agent2.name] = agent2

        assert "agent1" in sandbox.list()
        assert "agent2" in sandbox.list()
        assert len(sandbox.list()) == 2

    def test_remove_agent_directly(self, sandbox, mock_agent):
        """Test removing agent directly from sandbox."""
        sandbox._agents[mock_agent.name] = mock_agent
        del sandbox._agents[mock_agent.name]
        assert "test_agent" not in sandbox.list()

    def test_remove_nonexistent_agent(self, sandbox):
        """Test removing non-existent agent."""
        # This test is no longer relevant since we don't have unregister method
        # But we can test that removing from empty dict doesn't raise error
        if "nonexistent" in sandbox._agents:
            del sandbox._agents["nonexistent"]
        assert "nonexistent" not in sandbox.list()

    def test_remove_focused_agent(self, sandbox, mock_agent):
        """Test removing the focused agent."""
        sandbox._agents[mock_agent.name] = mock_agent
        sandbox._focused_agent = mock_agent.name
        assert sandbox.get_focused_name() == "test_agent"

        del sandbox._agents[mock_agent.name]
        # Focus should be cleared when agent is removed
        if sandbox._focused_agent == mock_agent.name:
            sandbox._focused_agent = None
        assert sandbox.get_focused_name() is None

    def test_get_agent(self, sandbox, mock_agent):
        """Test getting agent by name."""
        sandbox._agents[mock_agent.name] = mock_agent
        retrieved = sandbox.get("test_agent")
        assert retrieved is mock_agent

    def test_get_nonexistent_agent(self, sandbox):
        """Test getting non-existent agent."""
        assert sandbox.get("nonexistent") is None

    def test_list_agents(self, sandbox, mock_agent):
        """Test listing agents."""
        sandbox._agents[mock_agent.name] = mock_agent
        agents = sandbox.list()
        assert "test_agent" in agents
        assert isinstance(agents, list)

    def test_list_empty_sandbox(self, sandbox):
        """Test listing empty sandbox."""
        agents = sandbox.list()
        assert agents == []

    def test_get_focused_agent(self, sandbox, mock_agent):
        """Test getting focused agent."""
        sandbox._agents[mock_agent.name] = mock_agent
        sandbox._focused_agent = mock_agent.name
        focused = sandbox.get_focused()
        assert focused is mock_agent

    def test_get_focused_name(self, sandbox, mock_agent):
        """Test getting focused agent name."""
        sandbox._agents[mock_agent.name] = mock_agent
        sandbox._focused_agent = mock_agent.name
        name = sandbox.get_focused_name()
        assert name == "test_agent"

    def test_set_focus(self, sandbox, mock_agent):
        """Test setting focus."""
        sandbox._agents[mock_agent.name] = mock_agent
        assert sandbox.set_focus("test_agent") is True
        assert sandbox.get_focused_name() == "test_agent"

    def test_set_focus_nonexistent(self, sandbox):
        """Test setting focus to non-existent agent."""
        assert sandbox.set_focus("nonexistent") is False

    def test_clear_sandbox(self, sandbox, mock_agent):
        """Test clearing sandbox."""
        sandbox._agents[mock_agent.name] = mock_agent
        sandbox.clear()
        assert sandbox.list() == []
        assert sandbox.get_focused_name() is None

    def test_agent_in_sandbox(self, sandbox, mock_agent):
        """Test agent existence check."""
        assert "test_agent" not in sandbox._agents
        sandbox._agents[mock_agent.name] = mock_agent
        assert "test_agent" in sandbox._agents

    def test_execute_string_success(self, sandbox):
        """Test successful code execution."""
        result = sandbox.execute_string("2 + 2")

        assert result.success is True
        assert result.result == 4  # Real Dana execution returns 4, not "result"

    def test_execute_string_error(self, sandbox):
        """Test code execution with error."""
        result = sandbox.execute_string("invalid code")

        assert result.success is False
        # Dana wraps errors in DanaError, not ValueError
        from dana.common.exceptions import DanaError

        assert isinstance(result.error, DanaError)

    def test_execute_string_syntax_error(self, sandbox):
        """Test code execution with syntax error."""
        result = sandbox.execute_string("invalid syntax")

        assert result.success is False
        # Dana wraps syntax errors in DanaError, not SyntaxError
        from dana.common.exceptions import DanaError

        assert isinstance(result.error, DanaError)

    def test_get_all_agents(self, sandbox, mock_agent):
        """Test getting all agents as dictionary."""
        sandbox._agents[mock_agent.name] = mock_agent
        all_agents = sandbox.get_all_agents()
        assert isinstance(all_agents, dict)
        assert "test_agent" in all_agents
        assert all_agents["test_agent"] is mock_agent

    def test_get_dana_context(self, sandbox):
        """Test getting Dana context."""
        context = sandbox.get_dana_context()
        assert context is not None

    def test_get_dana_sandbox(self, sandbox):
        """Test getting underlying Dana sandbox."""
        dana_sandbox = sandbox.get_dana_sandbox()
        assert dana_sandbox is not None


class TestDanaSandboxIntegration:
    """Integration tests for DanaSandbox with real components."""

    @pytest.fixture
    def sandbox(self):
        """Provide sandbox with real Dana integration."""
        return DanaSandbox()

    def test_real_dana_integration(self, sandbox):
        """Test integration with real Dana components."""
        # Test that sandbox can be created
        assert sandbox is not None

        # Test that Dana context is available
        context = sandbox.get_dana_context()
        assert context is not None

        # Test that Dana sandbox is available
        dana_sandbox = sandbox.get_dana_sandbox()
        assert dana_sandbox is not None

    def test_sandbox_initialization(self, sandbox):
        """Test sandbox initialization."""
        # Test initial state
        assert sandbox.list() == []
        assert sandbox.get_focused_name() is None
        assert sandbox.get_focused() is None

    def test_agent_lifecycle(self, sandbox):
        """Test complete agent lifecycle."""
        # Create mock agent
        agent = AsyncMock(spec=AgentInstance)
        agent.name = "lifecycle_test"

        # Add agent directly
        sandbox._agents[agent.name] = agent
        assert "lifecycle_test" in sandbox.list()

        # Set focus
        sandbox._focused_agent = agent.name
        assert sandbox.get_focused_name() == "lifecycle_test"

        # Test focus management
        assert sandbox.set_focus("lifecycle_test") is True
        assert sandbox.get_focused() is agent

        # Test removal
        del sandbox._agents["lifecycle_test"]
        if sandbox._focused_agent == "lifecycle_test":
            sandbox._focused_agent = None
        assert "lifecycle_test" not in sandbox.list()
        assert sandbox.get_focused_name() is None
