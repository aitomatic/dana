"""Pytest configuration file."""

import os

import pytest


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption("--run-llm", action="store_true", default=False, help="Run tests that require LLM calls")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "llm: mark test as requiring an LLM connection")
    config.addinivalue_line("markers", "live: mark test as requiring external services (deselect with '-m \"not live\"')")


def pytest_collection_modifyitems(config, items):
    """Skip llm-marked tests unless --run-llm is provided."""
    if not config.getoption("--run-llm"):
        skip_llm = pytest.mark.skip(reason="Need --run-llm option to run LLM tests")
        for item in items:
            if "llm" in item.keywords:
                item.add_marker(skip_llm)


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
        os.environ["OPENDXA_MOCK_LLM"] = "true"
        yield
        del os.environ["OPENDXA_MOCK_LLM"]
    else:
        # When running live tests, ensure mock mode is disabled
        original_value = os.environ.get("OPENDXA_MOCK_LLM")
        if original_value:
            del os.environ["OPENDXA_MOCK_LLM"]
        yield
        if original_value:
            os.environ["OPENDXA_MOCK_LLM"] = original_value
