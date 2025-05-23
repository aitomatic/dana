"""Pytest configuration file."""

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
