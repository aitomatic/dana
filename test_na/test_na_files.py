"""
Universal Dana (.na) file test runner for test_na directory.

This file enables pytest to discover and run all test_*.na files in the test_na directory,
including subdirectories like 01_basic_syntax and 02_advanced_syntax.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
import signal
import subprocess
import time
from pathlib import Path

import pytest
import requests

from tests.conftest import run_dana_test_file

# Global variable to store MCP server process
mcp_server_process = None


def kill_process_on_port(port):
    """Kill any process using the specified port."""
    try:
        # Find process using the port
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False)

        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    print(f"Killing process {pid} using port {port}")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(0.5)  # Give it time to terminate

                    # Force kill if still running
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already terminated

    except (subprocess.SubprocessError, ValueError, OSError) as e:
        print(f"Warning: Could not kill process on port {port}: {e}")


def start_mcp_server():
    """Start the MCP HTTP server for integration tests."""
    global mcp_server_process

    if mcp_server_process is not None:
        return  # Server already running

    # Kill any existing process on port 8000
    kill_process_on_port(8000)

    server_script = Path(__file__).parent / "08_integration" / "python" / "start_http_streamable_server.py"

    # Start server in background
    mcp_server_process = subprocess.Popen(
        ["python3", str(server_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,  # Allow killing process group
    )

    # Wait for server to start
    max_retries = 5
    retry_delay = 1
    server_url = "http://localhost:8000/mcp"

    for _ in range(max_retries):
        try:
            requests.get(server_url)
            return
        except requests.exceptions.ConnectionError:
            time.sleep(retry_delay)

    raise RuntimeError("Failed to start MCP server")


def stop_mcp_server():
    """Stop the MCP HTTP server."""
    global mcp_server_process

    if mcp_server_process is not None:
        # Kill the entire process group
        os.killpg(os.getpgid(mcp_server_process.pid), signal.SIGTERM)
        mcp_server_process = None
        print("MCP server stopped")


def pytest_generate_tests(metafunc):
    """
    Custom test generation to discover all .na files in test_na directory and subdirectories.

    This overrides the default conftest.py behavior to find all .na files
    in the test_na directory tree.
    """
    if "dana_test_file" in metafunc.fixturenames:
        # Get the test_na directory (parent of this file)
        test_na_dir = Path(__file__).parent

        # Find all .na files recursively in test_na directory and subdirectories
        na_files = list(test_na_dir.rglob("*.na"))

        if na_files:
            # Create test IDs from relative paths for better reporting
            test_ids = [f.relative_to(test_na_dir).as_posix() for f in na_files]
            metafunc.parametrize("dana_test_file", na_files, ids=test_ids)


@pytest.mark.dana
def test_dana_files(dana_test_file):
    """
    Universal test that runs any Dana (.na) test file in test_na directory.

    This test is automatically parametrized by the pytest_generate_tests function
    above to run once for each test_*.na file in the test_na directory tree.

    For integration tests in 08_integration directory, it starts the MCP server
    before running the tests and stops it afterward.
    """
    try:
        # Start MCP server for integration tests
        if "test_mcp" in str(dana_test_file):
            start_mcp_server()

        # Run the test file
        run_dana_test_file(dana_test_file)

    finally:
        # Stop MCP server if it was started
        if "test_mcp" in str(dana_test_file):
            stop_mcp_server()
