"""
Universal Dana (.na) file test runner.

This file can be copied to any test directory that contains .na files.
It will automatically discover and run all test_*.na files in the same directory.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest
from tests.conftest import run_dana_test_file


@pytest.mark.dana
def test_dana_files(dana_test_file):
    """
    Universal test that runs any Dana (.na) test file.

    This test is automatically parametrized by the pytest_generate_tests function
    in conftest.py to run once for each test_*.na file in this directory.
    """
    run_dana_test_file(dana_test_file)
