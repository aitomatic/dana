import os

import pytest


@pytest.fixture(scope="session")
def api_service():
    """Configure API service for POET tests using APIServiceManager"""
    print("\n🔧 Setting up API service for POET tests...")

    # Set environment for APIServiceManager to use port 12345
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    print("✅ API service configured for http://localhost:12345")

    # APIServiceManager will handle the actual server startup when DanaSandbox is used
    yield

    print("\n🧹 API service configuration cleaned up")


@pytest.fixture(autouse=True)
def set_api_url(api_service):
    """Set the AITOMATIC_API_URL environment variable for all tests"""
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    print("🔧 AITOMATIC_API_URL set to http://localhost:12345")


def pytest_sessionstart(session):
    """Set environment variables at the start of the session."""
    os.environ["AITOMATIC_API_URL"] = "http://localhost:12345"
    print("🔧 AITOMATIC_API_URL set to http://localhost:12345")
