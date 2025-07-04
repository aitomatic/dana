"""Pytest fixtures for interpreter tests."""

import logging
from unittest.mock import patch

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def shared_sandbox():
    """Session-scoped fixture providing a shared DanaSandbox instance."""
    logger.debug("Creating shared DanaSandbox for session")
    sandbox = DanaSandbox()
    sandbox._ensure_initialized()
    yield sandbox
    logger.debug("Cleaning up shared DanaSandbox")


@pytest.fixture
def fresh_sandbox():
    """Function-scoped fixture providing a fresh DanaSandbox instance when needed."""
    logger.debug("Creating fresh DanaSandbox for test")
    sandbox = DanaSandbox()
    sandbox._ensure_initialized()
    yield sandbox


@pytest.fixture
def mock_sandbox():
    """Fixture to provide a mocked DanaSandbox instance."""
    with patch("opendxa.dana.sandbox.dana_sandbox.DanaSandbox._ensure_initialized"):
        sandbox = DanaSandbox()
        yield sandbox
