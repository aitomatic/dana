"""Pytest configuration file."""

import logging
import os
from pathlib import Path

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption("--run-llm", action="store_true", default=False, help="Run tests that require LLM calls")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "llm: mark test as requiring an LLM connection")
    config.addinivalue_line("markers", "live: mark test as requiring external services (deselect with '-m \"not live\"')")
    config.addinivalue_line("markers", "na_file: mark tests that execute .na files")


def pytest_collection_modifyitems(config, items):
    """Skip llm-marked tests unless --run-llm is provided."""
    if not config.getoption("--run-llm"):
        skip_llm = pytest.mark.skip(reason="Need --run-llm option to run LLM tests")
        for item in items:
            if "llm" in item.keywords:
                item.add_marker(skip_llm)


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging levels for tests to reduce verbose output."""
    # Suppress verbose HTTP logs from httpx and similar libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("h11").setLevel(logging.WARNING)

    # Suppress Dana logs during tests to reduce noise
    # Set to ERROR to suppress the repetitive INFO-level cleanup messages
    logging.getLogger("dana").setLevel(logging.ERROR)

    # Suppress specific noisy loggers during tests
    logging.getLogger("dana.dana").setLevel(logging.ERROR)
    logging.getLogger("dana.common").setLevel(logging.ERROR)
    logging.getLogger("dana.api").setLevel(logging.ERROR)
    logging.getLogger("dana.common.resource.llm_resource").setLevel(logging.ERROR)
    logging.getLogger("dana.api.client").setLevel(logging.ERROR)
    logging.getLogger("dana.api.server").setLevel(logging.ERROR)

    # Allow critical errors to still show through
    # If you need to see specific warnings/info during debugging,
    # you can temporarily lower these levels or use:
    # pytest -s --log-cli-level=INFO tests/your_test.py

    yield


@pytest.fixture(scope="session", autouse=True)
def configure_llm_mocking(request):
    """
    Configure LLM mocking based on the --run-llm flag.

    If --run-llm is NOT provided, enable mock LLM mode for all tests.
    This prevents tests that indirectly initialize LLM resources from
    failing when no API keys are configured.

    If --run-llm is provided, we assume live credentials are set up
    and do not enable mock mode.
    """
    if not request.config.getoption("--run-llm"):
        os.environ["DANA_MOCK_LLM"] = "true"
        yield
        # Only delete if it exists
        if "DANA_MOCK_LLM" in os.environ:
            del os.environ["DANA_MOCK_LLM"]
    else:
        # When running live tests, ensure mock mode is disabled
        original_value = os.environ.get("DANA_MOCK_LLM")
        if original_value:
            del os.environ["DANA_MOCK_LLM"]
        yield
        if original_value:
            os.environ["DANA_MOCK_LLM"] = original_value


@pytest.fixture(scope="session", autouse=True)
def clear_promise_groups():
    """Clear Promise groups at the start of each test session to prevent bleeding."""
    from dana.core.concurrency.lazy_promise import _current_promise_group

    # Clear any existing Promise groups
    if hasattr(_current_promise_group, "group"):
        delattr(_current_promise_group, "group")

    yield

    # Clear again at the end of the session
    if hasattr(_current_promise_group, "group"):
        delattr(_current_promise_group, "group")


@pytest.fixture(autouse=True)
def clear_promise_groups_per_test():
    """Clear Promise groups before each test to prevent bleeding."""
    from dana.core.concurrency.lazy_promise import _current_promise_group

    # Clear any existing Promise groups before test
    if hasattr(_current_promise_group, "group"):
        delattr(_current_promise_group, "group")

    yield

    # Clear again after test
    if hasattr(_current_promise_group, "group"):
        delattr(_current_promise_group, "group")


# Universal Dana (.na) file test integration
def pytest_generate_tests(metafunc):
    """
    Universal Dana (.na) file test generator.

    This function automatically discovers and creates pytest tests for any .na files
    in the same directory as the test file. Works across all test directories.
    """
    if "dana_test_file" in metafunc.fixturenames:
        # Get the directory of the current test file
        test_file_path = Path(metafunc.module.__file__)
        test_dir = test_file_path.parent

        # Find all .na files in the same directory
        na_files = list(test_dir.glob("test_*.na"))

        if na_files:
            # Create test IDs from filenames for better reporting
            test_ids = [f.stem for f in na_files]
            metafunc.parametrize("dana_test_file", na_files, ids=test_ids)


@pytest.fixture(scope="session")
def api_server():
    """Session-scoped fixture that starts a single API server for the entire test session."""
    logger = logging.getLogger(__name__)
    logger.info("Starting session-wide API server")

    # Set environment variable for API server URL
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    logger.info("Set AITOMATIC_API_URL to http://localhost:12345")

    # Import and start the API server
    from dana.api.server.server import APIServiceManager

    # Create and start the API service
    api_service = APIServiceManager()
    api_service.startup()

    logger.info("Session-wide API server ready")
    yield api_service

    logger.info("Session ending - shutting down API server")
    api_service.shutdown()

    # Clean up environment variable
    if "AITOMATIC_API_URL" in os.environ:
        del os.environ["AITOMATIC_API_URL"]


@pytest.fixture
def fresh_dana_sandbox(api_server):
    """Provide a fresh DanaSandbox for each test, using the shared API server."""
    sandbox = DanaSandbox()
    try:
        yield sandbox
    finally:
        sandbox._cleanup()


# Universal Dana file test function
def run_dana_test_file(dana_test_file):
    """
    Universal function to run a Dana (.na) test file.

    This can be used in any test directory by creating a simple test function like:

    def test_dana_files(dana_test_file, fresh_dana_sandbox):
        from tests.conftest import run_dana_test_file
        run_dana_test_file(dana_test_file, fresh_dana_sandbox)
    """
    # Clear struct registry to ensure test isolation
    from dana.core.lang.interpreter.struct_system import MethodRegistry, StructTypeRegistry
    from dana.core.runtime.modules.core import initialize_module_system, reset_module_system

    StructTypeRegistry.clear()
    MethodRegistry.clear()

    # Initialize module system for tests that may use imports
    reset_module_system()
    initialize_module_system()

    # Clear Promise group to prevent bleeding between tests
    from dana.core.concurrency.lazy_promise import _current_promise_group

    # Clear the thread-local Promise group
    if hasattr(_current_promise_group, "group"):
        delattr(_current_promise_group, "group")

    sandbox = DanaSandbox()
    try:
        result = sandbox.run_file(dana_test_file)
        assert result.success, f"Dana test {dana_test_file.name} failed: {result.error}"
    finally:
        sandbox._cleanup()
        # Clear Promise group again after test
        if hasattr(_current_promise_group, "group"):
            delattr(_current_promise_group, "group")
