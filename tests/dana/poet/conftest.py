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
    """Session-scoped fixture providing a single DanaSandbox instance for the entire test session."""
    logger.info("Creating session-wide DanaSandbox - single server startup")

    # Create sandbox and initialize resources once for the entire session
    sandbox = DanaSandbox()
    sandbox._ensure_initialized()

    logger.info("Session-wide DanaSandbox ready - reusing for all tests")
    yield sandbox

    logger.info("Session ending - cleaning up shared DanaSandbox")
    sandbox._cleanup()


@pytest.fixture
def fresh_sandbox(shared_sandbox):
    """
    Function-scoped fixture that reuses the shared sandbox but provides test isolation.
    This gives you a 'fresh' context without creating new servers.
    """
    logger.debug("Providing fresh context using shared sandbox")

    # Reset the context to provide test isolation while reusing the same sandbox infrastructure
    original_context = shared_sandbox._context

    # Create a fresh context for this test
    from opendxa.dana.sandbox.sandbox_context import SandboxContext

    fresh_context = SandboxContext()
    fresh_context.interpreter = shared_sandbox._interpreter

    # Copy system resources from shared context to fresh context
    if original_context.get("system.api_client"):
        fresh_context.set("system.api_client", original_context.get("system.api_client"))
    if original_context.get("system.llm_resource"):
        fresh_context.set("system.llm_resource", original_context.get("system.llm_resource"))

    # Add feedback placeholder
    def feedback_placeholder(result, feedback_data):
        logger.info(f"Feedback received for result: {result} -> {feedback_data}")
        return True

    fresh_context.set("local.feedback", feedback_placeholder)

    # Temporarily swap the context
    shared_sandbox._context = fresh_context

    yield shared_sandbox

    # Restore the original context (optional - could leave fresh for next test)
    shared_sandbox._context = original_context
    logger.debug("Fresh context test completed")


def pytest_sessionstart(session):
    """Set environment variables at the start of the session."""
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    logger.debug("Session start: AITOMATIC_API_URL set to http://localhost:12345")


def pytest_sessionfinish(session, exitstatus):
    """Clean up all DanaSandbox instances at the end of the session."""
    logger.debug("Session finish: cleaning up all DanaSandbox instances")
    from opendxa.dana.sandbox.dana_sandbox import DanaSandbox

    DanaSandbox.cleanup_all()
