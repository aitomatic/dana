"""
Pytest configuration for Dana TUI tests.

Following Textual testing best practices:
- Configure async test support
- Set up test environment
- Provide common fixtures
- Support different test types

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio

import pytest
from textual.app import App

# Test markers


@pytest.fixture
async def dana_tui_pilot():
    """Provide DanaTUI with pilot for testing."""
    from dana.apps.tui import DanaTUI

    app = DanaTUI()
    async with app.run_test() as pilot:
        yield pilot


@pytest.fixture
async def basic_app_pilot():
    """Provide a basic Textual app with pilot for testing."""
    app = App()
    async with app.run_test() as pilot:
        yield pilot


@pytest.fixture
def mock_sandbox():
    """Provide a mock sandbox for testing."""
    from unittest.mock import AsyncMock

    sandbox = AsyncMock()
    sandbox.list.return_value = ["agent1", "agent2"]
    sandbox.get_focused_name.return_value = "agent1"
    sandbox.execute_string.return_value = "test result"
    sandbox.register = AsyncMock()
    sandbox.unregister = AsyncMock(return_value=True)
    sandbox.set_focus = AsyncMock(return_value=True)
    return sandbox


@pytest.fixture
def mock_agent():
    """Provide a mock agent for testing."""
    from collections.abc import AsyncIterator

    from dana.apps.tui.core.events import AgentEvent, Done, Status, Token
    from dana.builtin_types.agent import AgentInstance

    class MockAgent(AgentInstance):
        def __init__(self, name: str):
            super().__init__(name)

        async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
            """Mock chat implementation that yields proper events."""
            self._metrics["is_running"] = True
            self._metrics["current_step"] = "processing"

            # Yield status event
            yield Status("processing", f"Processing: {message}")

            # Simulate work
            await asyncio.sleep(0.01)  # Very short for testing

            # Yield token events
            response = f"Mock response to: {message}"
            for char in response:
                yield Token(char)
                await asyncio.sleep(0.001)  # Very short for testing

            # Update metrics
            self._metrics["is_running"] = False
            self._metrics["current_step"] = "completed"

            # Yield completion event
            yield Done()

    return MockAgent


@pytest.fixture
def slow_agent():
    """Provide a slow mock agent for testing timeouts."""
    from collections.abc import AsyncIterator

    from dana.apps.tui.core.events import AgentEvent, Done, Status, Token
    from dana.builtin_types.agent import AgentInstance

    class SlowMockAgent(AgentInstance):
        def __init__(self, name: str, delay: float = 0.1):
            super().__init__(name)
            self.delay = delay

        async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
            """Slow mock chat implementation."""
            self._metrics["is_running"] = True
            self._metrics["current_step"] = "processing"

            yield Status("processing", f"Processing: {message}")

            # Simulate slow work
            await asyncio.sleep(self.delay)

            response = f"Slow response to: {message}"
            for char in response:
                yield Token(char)
                await asyncio.sleep(self.delay / len(response))

            self._metrics["is_running"] = False
            self._metrics["current_step"] = "completed"
            yield Done()

    return SlowMockAgent


@pytest.fixture
def error_agent():
    """Provide an agent that raises errors for testing error handling."""
    from collections.abc import AsyncIterator

    from dana.apps.tui.core.events import AgentEvent, Error
    from dana.builtin_types.agent import AgentInstance

    class ErrorMockAgent(AgentInstance):
        def __init__(self, name: str, error_message: str = "Test error"):
            super().__init__(name)
            self.error_message = error_message

        async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
            """Mock chat implementation that raises errors."""
            self._metrics["is_running"] = True
            self._metrics["current_step"] = "error"

            yield Error(self.error_message)

            self._metrics["is_running"] = False
            self._metrics["current_step"] = "error"

    return ErrorMockAgent


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "token_flush_interval": 0.01,  # Fast for testing
        "update_throttle_interval": 0.01,  # Fast for testing
        "max_agents": 10,
        "enable_animations": False,  # Disable for testing
        "log_level": "ERROR",  # Reduce log noise
    }


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "tui: mark test as TUI-related")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "ui: mark test as UI component test")
    config.addinivalue_line("markers", "snapshot: mark test as snapshot test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "unit: mark test as unit test")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their characteristics."""
    for item in items:
        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Mark TUI-related tests
        if "tui" in item.nodeid:
            item.add_marker(pytest.mark.tui)

        # Mark UI component tests
        if "test_ui_components" in item.nodeid:
            item.add_marker(pytest.mark.ui)

        # Mark snapshot tests
        if "test_snapshots" in item.nodeid:
            item.add_marker(pytest.mark.snapshot)

        # Mark performance tests
        if "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)

        # Mark integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (default for core logic tests)
        if any(x in item.nodeid for x in ["test_runtime", "test_taskman", "test_router"]):
            item.add_marker(pytest.mark.unit)


# Convenience fixtures for common test patterns
@pytest.fixture
def slow():
    """Mark test as slow for selective running."""
    return pytest.mark.slow


@pytest.fixture
def integration():
    """Mark test as integration test."""
    return pytest.mark.integration


@pytest.fixture
def ui():
    """Mark test as UI test."""
    return pytest.mark.ui


@pytest.fixture
def snapshot():
    """Mark test as snapshot test."""
    return pytest.mark.snapshot


@pytest.fixture
def performance():
    """Mark test as performance test."""
    return pytest.mark.performance


@pytest.fixture
def unit():
    """Mark test as unit test."""
    return pytest.mark.unit
