"""
Test runner for singleton agent .na test files.

Automatically discovers and runs all test_*.na files in the singleton_agent directory.
"""

from pathlib import Path

import pytest

from tests.conftest import run_dana_test_file


def get_singleton_agent_na_files():
    """Get all .na test files in the singleton_agent directory."""
    test_dir = Path(__file__).parent / "singleton_agent"
    na_files = list(test_dir.glob("test_*.na"))
    return na_files


@pytest.mark.dana
@pytest.mark.parametrize("dana_test_file", get_singleton_agent_na_files(), ids=[f.stem for f in get_singleton_agent_na_files()])
def test_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file in singleton_agent."""
    run_dana_test_file(dana_test_file)
