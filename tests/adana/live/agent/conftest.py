"""
Pytest configuration for live agent tests

Live tests involve live resources (LLMs) and require real API keys.
"""

import asyncio
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Configure pytest with custom markers for agent tests."""
    config.addinivalue_line("markers", "live: marks tests as live tests that involve live resources (LLMs)")
    config.addinivalue_line("markers", "agent: marks tests as agent-related tests")
    config.addinivalue_line("markers", "star: marks tests as STAR pattern tests")
    config.addinivalue_line("markers", "multi_agent: marks tests as multi-agent tests")
    config.addinivalue_line("markers", "components: marks tests as component tests")
