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
from dana.apps.tui.core.runtime import Agent, DanaSandbox


class MockTestAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, name: str, response_text: str = "test response"):
        super().__init__(name)
        self.response_text = response_text
        self.chat_calls = []

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

    @pytest.fixture
    def test_agents(self):
        """Create test agents."""
        return [MockTestAgent("agent1", "response1"), MockTestAgent("agent2", "response2"), MockTestAgent("agent3", "response3")]

    def test_initial_state(self, sandbox):
        """Test sandbox initial state."""
        assert len(sandbox.list()) == 0
        assert sandbox.get_focused() is None
        assert sandbox.get_focused_name() is None

    def test_register_agent(self, sandbox, test_agents):
        """Test agent registration."""
        agent = test_agents[0]
        sandbox.register(agent)

        assert len(sandbox.list()) == 1
        assert agent.name in sandbox.list()
        assert sandbox.get(agent.name) is agent
        assert sandbox.exists(agent.name)

        # First agent should be auto-focused
        assert sandbox.get_focused() is agent
        assert sandbox.get_focused_name() == agent.name

    def test_register_multiple_agents(self, sandbox, test_agents):
        """Test registering multiple agents."""
        for agent in test_agents:
            sandbox.register(agent)

        assert len(sandbox.list()) == 3
        assert set(sandbox.list()) == {"agent1", "agent2", "agent3"}

        # First agent should still be focused
        assert sandbox.get_focused_name() == "agent1"

    def test_focus_switching(self, sandbox, test_agents):
        """Test focus switching between agents."""
        for agent in test_agents:
            sandbox.register(agent)

        # Initially focused on first agent
        assert sandbox.get_focused_name() == "agent1"

        # Switch focus
        result = sandbox.set_focus("agent2")
        assert result is True
        assert sandbox.get_focused_name() == "agent2"
        assert sandbox.get_focused() is test_agents[1]

        # Switch to another agent
        result = sandbox.set_focus("agent3")
        assert result is True
        assert sandbox.get_focused_name() == "agent3"

        # Try to focus non-existent agent
        result = sandbox.set_focus("nonexistent")
        assert result is False
        assert sandbox.get_focused_name() == "agent3"  # Should remain unchanged

    def test_unregister_agent(self, sandbox, test_agents):
        """Test agent unregistration."""
        for agent in test_agents:
            sandbox.register(agent)

        # Remove an agent that's not focused
        result = sandbox.unregister("agent2")
        assert result is True
        assert "agent2" not in sandbox.list()
        assert len(sandbox.list()) == 2
        assert sandbox.get_focused_name() == "agent1"  # Focus unchanged

        # Remove the focused agent
        result = sandbox.unregister("agent1")
        assert result is True
        assert "agent1" not in sandbox.list()
        assert len(sandbox.list()) == 1

        # Focus should switch to remaining agent
        assert sandbox.get_focused_name() == "agent3"

        # Remove last agent
        result = sandbox.unregister("agent3")
        assert result is True
        assert len(sandbox.list()) == 0
        assert sandbox.get_focused() is None

    def test_unregister_nonexistent_agent(self, sandbox):
        """Test unregistering non-existent agent."""
        result = sandbox.unregister("nonexistent")
        assert result is False

    def test_get_all_agents(self, sandbox, test_agents):
        """Test getting all agents."""
        for agent in test_agents:
            sandbox.register(agent)

        all_agents = sandbox.get_all_agents()
        assert len(all_agents) == 3
        assert all_agents["agent1"] is test_agents[0]
        assert all_agents["agent2"] is test_agents[1]
        assert all_agents["agent3"] is test_agents[2]

        # Should be a copy, not the original dict
        all_agents["new_agent"] = MockTestAgent("new_agent")
        assert "new_agent" not in sandbox.list()

    def test_clear_sandbox(self, sandbox, test_agents):
        """Test clearing all agents."""
        for agent in test_agents:
            sandbox.register(agent)

        assert len(sandbox.list()) == 3
        assert sandbox.get_focused() is not None

        sandbox.clear()

        assert len(sandbox.list()) == 0
        assert sandbox.get_focused() is None
        assert sandbox.get_focused_name() is None

    def test_focus_management_edge_cases(self, sandbox, test_agents):
        """Test edge cases in focus management."""
        # Set focus with no agents
        result = sandbox.set_focus("agent1")
        assert result is False
        assert sandbox.get_focused() is None

        # Register first agent
        sandbox.register(test_agents[0])
        assert sandbox.get_focused_name() == "agent1"

        # Register second agent - focus should stay on first
        sandbox.register(test_agents[1])
        assert sandbox.get_focused_name() == "agent1"

        # Remove focused agent when only one other exists
        sandbox.unregister("agent1")
        assert sandbox.get_focused_name() == "agent2"

        # Remove last agent
        sandbox.unregister("agent2")
        assert sandbox.get_focused() is None

    def test_agent_name_collision(self, sandbox):
        """Test handling of agent name collisions."""
        agent1 = MockTestAgent("same_name")
        agent2 = MockTestAgent("same_name")

        sandbox.register(agent1)
        assert sandbox.get("same_name") is agent1

        # Registering another agent with same name should replace
        sandbox.register(agent2)
        assert sandbox.get("same_name") is agent2
        assert len(sandbox.list()) == 1

    @pytest.mark.asyncio
    async def test_agent_interaction_through_sandbox(self, sandbox):
        """Test agent interaction through the sandbox."""
        agent = MockTestAgent("test_agent", "sandbox response")
        sandbox.register(agent)

        focused_agent = sandbox.get_focused()
        assert focused_agent is agent

        # Interact with the focused agent
        events = []
        async for event in focused_agent.chat("test message"):
            events.append(event)

        # Verify the interaction worked
        assert len(events) >= 3
        token_chars = [event.text for event in events if isinstance(event, Token)]
        assert "".join(token_chars) == "sandbox response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
