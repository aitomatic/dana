import os
import subprocess
import time

import pytest


@pytest.fixture(scope="session")
def api_service():
    print("\n🔧 Setting up API service for POET tests...")
    print(f"PATH: {os.environ.get('PATH')}")
    # Launch the API service
    service_process = subprocess.Popen(
        [".venv/bin/python", "-m", "opendxa.api.service_manager"], env={"AITOMATIC_API_URL": "http://localhost:8080"}
    )
    time.sleep(5)  # Wait for the service to start
    print("✅ API service started at http://localhost:8080")
    yield
    print("\n🧹 Cleaning up API service...")
    # Cleanup: terminate the service
    service_process.terminate()
    service_process.wait()
    print("✅ API service terminated")


@pytest.fixture(autouse=True)
def set_api_url(api_service):
    # Set the AITOMATIC_API_URL environment variable for all tests
    os.environ["AITOMATIC_API_URL"] = "http://localhost:8080"
    print("🔧 AITOMATIC_API_URL set to http://localhost:8080")
