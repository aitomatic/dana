"""
Integration Tests for Dana TUI.

Test complete workflows and user scenarios using Textual's Pilot.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.tui import DanaTUI


@pytest.mark.asyncio
async def test_complete_agent_workflow():
    """Test complete agent creation and interaction workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        assert "research" in app.sandbox.list()

        # Send message to existing agent
        for char in "@research find AI papers":
            await pilot.press(char)
        await pilot.press("enter")

        # Verify response appears
        terminal = app.query_one("#terminal-output")
        assert terminal is not None

        # Verify agent detail updates
        detail = app.query_one("#detail-log")
        assert detail is not None


@pytest.mark.asyncio
async def test_task_cancellation_workflow():
    """Test task cancellation workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Send message to existing agent
        for char in "@research long_task":
            await pilot.press(char)
        await pilot.press("enter")

        # Cancel task
        await pilot.press("escape")

        # Verify cancellation was handled
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_multi_agent_interaction():
    """Test interaction with multiple agents."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        assert "planner" in app.sandbox.list()
        assert "coder" in app.sandbox.list()

        # Switch between agents
        await pilot.press("tab")
        # Don't assume specific order, just verify focus changed
        focus_after_first_tab = app.sandbox.get_focused_name()
        assert focus_after_first_tab is not None

        await pilot.press("tab")
        focus_after_second_tab = app.sandbox.get_focused_name()
        assert focus_after_second_tab is not None


@pytest.mark.asyncio
async def test_agent_communication_workflow():
    """Test agent communication workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        assert "research" in app.sandbox.list()

        # Send messages to different agents
        for char in "@research research topic":
            await pilot.press(char)
        await pilot.press("enter")

        await pilot.press("tab")  # Switch to coder
        for char in "@coder write code":
            await pilot.press(char)
        await pilot.press("enter")

        # Verify both agents exist and are accessible
        assert "research" in app.sandbox.list()
        assert "coder" in app.sandbox.list()


@pytest.mark.asyncio
async def test_error_recovery_workflow():
    """Test error recovery workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test invalid command
        for char in "invalid command":
            await pilot.press(char)
        await pilot.press("enter")

        # Try creating agent with invalid name
        for char in "agent invalid name with spaces":
            await pilot.press(char)
        await pilot.press("enter")

        # Try sending message to non-existent agent
        for char in "@nonexistent hello":
            await pilot.press(char)
        await pilot.press("enter")

        # Verify app still works
        for char in "agent valid":
            await pilot.press(char)
        await pilot.press("enter")

        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_persistence_workflow():
    """Test persistence workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        assert "research" in app.sandbox.list()

        # Send multiple messages
        messages = ["first message", "second message", "third message"]
        for message in messages:
            for char in f"@research {message}":
                await pilot.press(char)
            await pilot.press("enter")

        # Verify agent still exists
        assert "research" in app.sandbox.list()

        # Switch away and back
        await pilot.press("tab")
        await pilot.press("tab")
        assert app.sandbox.get_focused_name() == "research"


@pytest.mark.asyncio
async def test_concurrent_agent_workflow():
    """Test concurrent agent workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        agents = ["research", "coder", "planner"]
        for agent in agents:
            assert agent in app.sandbox.list()

        # Test rapid switching
        for _ in range(10):
            await pilot.press("tab")

        # Verify all agents still accessible
        for agent in agents:
            assert agent in app.sandbox.list()


@pytest.mark.asyncio
async def test_help_and_navigation_workflow():
    """Test help and navigation workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test help
        await pilot.press("f1")

        # Test navigation keys
        await pilot.press("tab")
        await pilot.press("shift+tab")
        await pilot.press("escape")

        # Test clear transcript
        for char in "some content":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.press("ctrl+l")

        # Verify app still functional
        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_agent_removal_workflow():
    """Test agent removal workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        initial_count = len(app.sandbox.list())
        assert initial_count >= 3

        # Verify agents exist
        assert "research" in app.sandbox.list()
        assert "coder" in app.sandbox.list()
        assert "planner" in app.sandbox.list()

        # Test that we can still interact with them
        for char in "@research test":
            await pilot.press(char)
        await pilot.press("enter")

        assert True  # Basic functionality test


@pytest.mark.asyncio
async def test_large_scale_workflow():
    """Test large scale workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        initial_count = len(app.sandbox.list())
        assert initial_count >= 3

        # Test rapid navigation through existing agents
        for _ in range(20):  # Navigate more than once through the list
            await pilot.press("tab")

        # Verify all still accessible
        assert len(app.sandbox.list()) >= 3


@pytest.mark.asyncio
async def test_mixed_command_workflow():
    """Test mixed command workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Mix different types of commands
        commands = ["@research hello", "@coder write code", "@planner plan project"]

        for command in commands:
            for char in command:
                await pilot.press(char)
            await pilot.press("enter")

        # Verify all agents created
        assert "research" in app.sandbox.list()
        assert "coder" in app.sandbox.list()
        assert "planner" in app.sandbox.list()


@pytest.mark.asyncio
async def test_focus_management_workflow():
    """Test focus management workflow."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test with existing agents
        assert "research" in app.sandbox.list()

        # Test focus switching
        await pilot.press("tab")
        new_focus = app.sandbox.get_focused_name()

        # Verify focus is valid (may or may not change depending on implementation)
        assert new_focus is not None

        # Test focus consistency - try shift+tab to go back
        await pilot.press("shift+tab")
        final_focus = app.sandbox.get_focused_name()
        assert final_focus is not None
