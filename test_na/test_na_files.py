"""
Universal Dana (.na) file test runner for test_na directory.

This file enables pytest to discover and run all test_*.na files in the test_na directory,
including subdirectories like 01_basic_syntax and 02_advanced_syntax.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

import pytest

from tests.conftest import run_dana_test_file


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
    above to run once for each test_*.na file in the 01_basic_syntax and
    02_advanced_syntax subdirectories.
    """
    run_dana_test_file(dana_test_file)
