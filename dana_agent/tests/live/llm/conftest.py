"""
Pytest configuration for LLM provider tests
"""

import asyncio
from collections.abc import Generator

import pytest


# Test message for all providers
TEST_MESSAGE = "Hello! Please respond with just 'Hi there!' to confirm the connection works."

# Expected response patterns (case insensitive)
EXPECTED_RESPONSE_PATTERNS = ["hi there", "hello", "hi", "connection works", "test successful"]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "live: marks tests as live tests that make real API calls")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "provider: marks tests for specific providers")
