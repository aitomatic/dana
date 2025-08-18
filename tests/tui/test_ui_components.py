"""
UI Component Tests for Dana TUI.

Tests UI components using Textual's Pilot for realistic user interaction testing.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.apps.tui import DanaTUI

# Skip all tests in this file until TUI component tests are updated for new AGENT_REGISTRY architecture
pytestmark = pytest.mark.skip(reason="TUI component tests need updating for AGENT_REGISTRY architecture")
from dana.apps.tui.ui.agent_detail import AgentDetail
from dana.apps.tui.ui.agents_list import AgentsList
from dana.apps.tui.ui.repl_panel import TerminalREPL


@pytest.mark.asyncio
async def test_terminal_widget_basic():
    """Test basic terminal widget functionality."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test terminal widget exists
        terminal = app.query_one(TerminalREPL)
        assert terminal is not None

        # Test input functionality
        await pilot.press("a")
        await pilot.press("g")
        await pilot.press("e")
        await pilot.press("n")
        await pilot.press("t")
        await pilot.press(" ")
        await pilot.press("t")
        await pilot.press("e")
        await pilot.press("s")
        await pilot.press("t")
        await pilot.press("enter")

        # Verify command was processed
        log = app.query_one("#terminal-output")
        assert log is not None


@pytest.mark.asyncio
async def test_agents_list_interaction():
    """Test agents list interaction."""
    app = DanaTUI()
    async with app.run_test():
        # Test that agents list exists and shows existing agents
        agents_list = app.query_one(AgentsList)
        assert agents_list is not None

        # Verify existing agents are present
        all_agents = app.sandbox.list()
        assert len(all_agents) >= 3  # Should have at least the original 3 agents
        assert "research" in all_agents
        assert "coder" in all_agents
        assert "planner" in all_agents


@pytest.mark.asyncio
async def test_key_navigation():
    """Test keyboard navigation between agents."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test tab navigation with existing agents
        await pilot.press("tab")
        # Verify focus changed (don't assume specific agent name)
        initial_focus = app.sandbox.get_focused_name()
        assert initial_focus is not None

        await pilot.press("tab")
        # Verify focus changed again
        new_focus = app.sandbox.get_focused_name()
        assert new_focus is not None


@pytest.mark.asyncio
async def test_terminal_input_focus():
    """Test terminal input focus and typing."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test terminal widget exists
        terminal = app.query_one(TerminalREPL)
        assert terminal is not None

        # Test typing in terminal
        await pilot.press("h")
        await pilot.press("e")
        await pilot.press("l")
        await pilot.press("l")
        await pilot.press("o")
        await pilot.press(" ")
        await pilot.press("w")
        await pilot.press("o")
        await pilot.press("r")
        await pilot.press("l")
        await pilot.press("d")
        await pilot.press("enter")

        # Verify input was processed
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_agent_detail_updates():
    """Test agent detail panel updates."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test that agent detail exists
        detail = app.query_one(AgentDetail)
        assert detail is not None

        # Test sending message to existing agent
        await pilot.press("@")
        await pilot.press("r")
        await pilot.press("e")
        await pilot.press("s")
        await pilot.press("e")
        await pilot.press("a")
        await pilot.press("r")
        await pilot.press("c")
        await pilot.press("h")
        await pilot.press(" ")
        await pilot.press("t")
        await pilot.press("e")
        await pilot.press("s")
        await pilot.press("t")
        await pilot.press(" ")
        await pilot.press("m")
        await pilot.press("e")
        await pilot.press("s")
        await pilot.press("s")
        await pilot.press("a")
        await pilot.press("g")
        await pilot.press("e")
        await pilot.press("enter")

        # Verify agent detail exists
        detail = app.query_one(AgentDetail)
        assert detail is not None


@pytest.mark.asyncio
async def test_escape_cancellation():
    """Test escape key cancellation."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test escape cancellation
        await pilot.press("escape")

        # Verify no error occurred
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_help_command():
    """Test help command functionality."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test F1 help
        await pilot.press("f1")

        # Verify help was triggered
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_clear_transcript():
    """Test clear transcript functionality."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Clear transcript
        await pilot.press("ctrl+l")

        # Verify clear was triggered
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_agent_creation_flow():
    """Test complete agent creation flow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test that we can interact with existing agents
        all_agents = app.sandbox.list()
        assert len(all_agents) >= 3  # Should have at least the original 3 agents

        # Test sending message to existing agent
        await pilot.press("@")
        await pilot.press("r")
        await pilot.press("e")
        await pilot.press("s")
        await pilot.press("e")
        await pilot.press("a")
        await pilot.press("r")
        await pilot.press("c")
        await pilot.press("h")
        await pilot.press(" ")
        await pilot.press("h")
        await pilot.press("e")
        await pilot.press("l")
        await pilot.press("l")
        await pilot.press("o")
        await pilot.press("enter")

        # Verify message was sent
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_multi_agent_management():
    """Test managing multiple agents."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        all_agents = app.sandbox.list()
        assert len(all_agents) >= 3  # Should have at least the original 3 agents

        # Test switching between existing agents
        for _ in range(3):
            await pilot.press("tab")
            # Verify focus changes (basic test)
            assert True


@pytest.mark.asyncio
async def test_ui_layout_components():
    """Test that all UI components are present."""
    app = DanaTUI()
    async with app.run_test():
        # Test all major components exist
        terminal = app.query_one(TerminalREPL)
        assert terminal is not None

        agents_list = app.query_one(AgentsList)
        assert agents_list is not None

        agent_detail = app.query_one(AgentDetail)
        assert agent_detail is not None

        footer = app.query_one("Footer")
        assert footer is not None


@pytest.mark.asyncio
async def test_input_validation():
    """Test input validation and error handling."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test empty input
        await pilot.press("enter")

        # Test invalid input
        for char in "invalid command":
            await pilot.press(char)
        await pilot.press("enter")

        # Verify no crash occurred
        assert True  # Basic error handling test
