"""
Test runner for agent blueprint .na test files.

Automatically discovers and runs all test_*.na files in the agent_blueprint directory.
"""

from pathlib import Path

import pytest

from tests.conftest import run_dana_test_file


def get_agent_blueprint_na_files():
    """Get all .na test files in the agent_blueprint directory."""
    test_dir = Path(__file__).parent / "agent_blueprint"
    na_files = list(test_dir.glob("test_*.na"))
    return na_files


@pytest.mark.dana
def test_agent_blueprint_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file in agent_blueprint."""
    # Only run tests from the agent_blueprint subdirectory
    if "agent_blueprint" not in str(dana_test_file):
        pytest.skip(f"Skipping {dana_test_file.name} - not in agent_blueprint directory")
    run_dana_test_file(dana_test_file)
