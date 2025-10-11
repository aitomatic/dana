"""
Pytest configuration for LLM tests
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
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "functional: marks tests as functional tests")
    config.addinivalue_line("markers", "regression: marks tests as regression tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "provider: marks tests for specific providers")
    config.addinivalue_line("markers", "live: marks tests as live tests that involve live resources (LLMs)")
    config.addinivalue_line("markers", "requires_api_keys: marks tests as requiring API keys (skip in CI without keys)")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption("--live", action="store_true", default=False, help="Run live tests that involve live resources (LLMs)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    if not config.getoption("--live"):
        # If --live flag is not provided, skip live tests
        skip_live = pytest.mark.skip(reason="Live tests require --live flag")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
    else:
        # If --live flag is provided, only run live tests
        skip_non_live = pytest.mark.skip(reason="Only live tests are run with --live flag")
        for item in items:
            if "live" not in item.keywords:
                item.add_marker(skip_non_live)
