"""
Test runner for a2a agent .na test files.

Automatically discovers and runs all test_*.na files in the a2a_agent directory.
"""

from pathlib import Path

import pytest

from tests.conftest import run_dana_test_file


def get_a2a_agent_na_files():
    """Get all .na test files in the a2a_agent directory."""
    test_dir = Path(__file__).parent / "a2a_agent"
    na_files = list(test_dir.glob("test_*.na"))
    return na_files


@pytest.mark.dana
@pytest.mark.parametrize("dana_test_file", get_a2a_agent_na_files(), ids=[f.stem for f in get_a2a_agent_na_files()])
def test_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file in a2a_agent."""
    run_dana_test_file(dana_test_file)
