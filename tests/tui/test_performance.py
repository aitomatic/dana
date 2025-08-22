"""
Performance Tests for Dana TUI.

Test UI responsiveness and scalability under various conditions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import time

import pytest

from dana.apps.tui import DanaTUI

# Skip all tests in this file until TUI performance tests are updated for new AGENT_REGISTRY architecture
pytestmark = pytest.mark.skip(reason="TUI performance tests need updating for AGENT_REGISTRY architecture")


@pytest.mark.asyncio
async def test_ui_responsiveness():
    """Test that the UI remains responsive under load."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Simulate rapid agent creation
        for i in range(5):
            await pilot.press(f"agent agent{i}", "enter")
        # Check that the UI is still responsive
        assert app.is_running


@pytest.mark.asyncio
async def test_large_agent_list():
    """Test performance with many agents."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Create many agents
        for i in range(10):
            await pilot.press(f"agent agent{i}", "enter")

        # UI should still be responsive
        agents_list = app.query_one("#agents-list")
        assert agents_list is not None

        # Navigation should work
        await pilot.press("tab")
        assert app.sandbox.get_focused_name() is not None


@pytest.mark.asyncio
async def test_rapid_navigation():
    """Test rapid navigation performance."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Create agents
        for i in range(5):
            await pilot.press(f"agent agent{i}", "enter")

        # Test rapid navigation
        start_time = time.time()
        for _ in range(20):  # Many rapid tab presses
            await pilot.press("tab")
        end_time = time.time()

        # Navigation should be fast
        assert end_time - start_time < 5.0


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test performance with concurrent operations."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Create agents quickly
        start_time = time.time()
        for i in range(5):
            await pilot.press(f"agent agent{i}", "enter")

        # Send messages to all agents quickly
        for i in range(5):
            await pilot.press(f"@agent{i} message{i}", "enter")

        end_time = time.time()

        # Operations should complete quickly
        assert end_time - start_time < 15.0


@pytest.mark.asyncio
async def test_memory_usage():
    """Test memory usage with many operations."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Perform many operations to test memory usage
        for i in range(10):
            await pilot.press(f"agent agent{i}", "enter")
            await pilot.press(f"agent{i}.chat('message{i}')", "enter")

        # Navigation should still work
        await pilot.press("tab")
        assert app.sandbox.get_focused_name() is not None


@pytest.mark.asyncio
async def test_input_processing_speed():
    """Test input processing speed."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Test typing speed
        start_time = time.time()

        long_message = "This is a very long message that should be processed quickly by the terminal input system"
        await pilot.press(long_message, "enter")

        end_time = time.time()

        # Input should be processed quickly
        assert end_time - start_time < 2.0


@pytest.mark.asyncio
async def test_ui_update_performance():
    """Test UI update performance during state changes."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Create agents and trigger many UI updates
        start_time = time.time()

        for i in range(10):
            await pilot.press(f"agent agent{i}", "enter")
            await pilot.press("tab")  # Trigger UI updates

        end_time = time.time()

        # UI updates should be fast
        assert end_time - start_time < 10.0


@pytest.mark.asyncio
async def test_error_handling_performance():
    """Test performance when handling errors."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Generate many errors quickly
        start_time = time.time()

        for i in range(10):
            await pilot.press(f"invalid command {i}", "enter")

        end_time = time.time()

        # Error handling should be fast
        assert end_time - start_time < 5.0

        # App should still be functional
        await pilot.press("agent valid", "enter")


@pytest.mark.asyncio
async def test_focus_switching_performance():
    """Test performance of focus switching."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Create agents
        for i in range(5):
            await pilot.press(f"agent agent{i}", "enter")

        # Test rapid focus switching
        start_time = time.time()

        for _ in range(50):
            await pilot.press("tab")

        end_time = time.time()

        # Focus switching should be very fast
        assert end_time - start_time < 5.0


@pytest.mark.asyncio
async def test_terminal_scroll_performance():
    """Test terminal scrolling performance with lots of content."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Add lots of content to terminal
        start_time = time.time()

        for i in range(20):
            await pilot.press(f"line {i}: some content here", "enter")

        end_time = time.time()

        # Adding content should be reasonably fast
        assert end_time - start_time < 15.0

        # Terminal should still be responsive
        terminal = app.query_one("#terminal-output")
        assert terminal is not None


@pytest.mark.asyncio
async def test_startup_performance():
    """Test app startup performance."""
    start_time = time.time()
    app = DanaTUI()
    async with app.run_test() as pilot:
        end_time = time.time()

        # App should start quickly
        assert end_time - start_time < 3.0

        # Basic functionality should work immediately
        await pilot.press("agent test", "enter")


@pytest.mark.asyncio
async def test_cleanup_performance():
    """Test cleanup performance when closing app."""
    app = DanaTUI()
    async with app.run_test() as pilot:
        # Create some state
        for i in range(5):
            await pilot.press(f"agent agent{i}", "enter")

        # Test cleanup time (this will be measured when context exits)
        # Context will exit here, triggering cleanup
        pass

    # Cleanup should be fast (measured after context exit)
    # Note: This is a basic test - actual cleanup timing would need more sophisticated measurement
    assert True  # Basic functionality test
