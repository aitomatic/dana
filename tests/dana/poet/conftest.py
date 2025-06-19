import logging
import os

import pytest

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def api_service():
    """Configure API service for POET tests using APIServiceManager"""
    logger.debug("Setting up API service for POET tests...")

    # Set environment for APIServiceManager to use port 12345
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    logger.debug("API service configured for http://localhost:12345")

    # APIServiceManager will handle the actual server startup when DanaSandbox is used
    yield

    logger.debug("API service configuration cleaned up")


@pytest.fixture(scope="session", autouse=True)
def set_api_url_session():
    """Set the AITOMATIC_API_URL environment variable for the entire session"""
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    logger.debug("Session-level AITOMATIC_API_URL set to http://localhost:12345")
    yield
    # Clean up after session
    if "AITOMATIC_API_URL" in os.environ:
        del os.environ["AITOMATIC_API_URL"]


@pytest.fixture(scope="session")
def shared_sandbox(api_service):
    """Session-scoped fixture providing a shared DanaSandbox instance for POET tests."""
    logger.debug("Creating shared DanaSandbox for POET session")
    sandbox = DanaSandbox()
    sandbox._ensure_initialized()
    yield sandbox
    logger.debug("Cleaning up shared DanaSandbox for POET")


@pytest.fixture
def fresh_sandbox(api_service):
    """Function-scoped fixture providing a fresh DanaSandbox instance when needed."""
    logger.debug("Creating fresh DanaSandbox for POET test")
    sandbox = DanaSandbox()
    sandbox._ensure_initialized()
    yield sandbox


def pytest_sessionstart(session):
    """Set environment variables at the start of the session."""
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    logger.debug("Session start: AITOMATIC_API_URL set to http://localhost:12345")
