"""
Test runner for language limitation .na files using pytest.

This test runner automatically discovers and executes test_*.na files in the
tests/dana/expected_failures/language_limitations/ directory, marking them as expected
failures to document known Dana language limitations.
"""

from pathlib import Path

import pytest

# Test files that are expected to fail due to language limitations
# Each entry is (subdirectory, filename) relative to tests/dana/expected_failures/
EXPECTED_FAILURE_FILES = [
    ("syntax_limitations", "test_expected_syntax_failures.na"),
    ("data_structure_limitations", "test_expected_data_structure_failures.na"),
    ("function_limitations", "test_expected_function_failures.na"),
    ("operator_limitations", "test_expected_operator_failures.na"),
    # NOTE: test_expected_fstring_limitations.na removed - f-strings now work correctly
]


class TestDanaLanguageLimitations:
    """Test suite for Dana language limitations documented in .na files."""

    @pytest.mark.parametrize("test_file", EXPECTED_FAILURE_FILES)
    @pytest.mark.xfail(reason="Expected language limitation - documents current Dana parser constraints")
    def test_expected_failures(self, test_file, fresh_dana_sandbox):
        """
        Execute expected failure .na files to document language limitations.

        These tests are marked as expected failures (xfail) to:
        1. Document current Dana language limitations
        2. Track which features need implementation
        3. Provide regression tests for future improvements
        4. Pass CI/CD while documenting gaps

        When these tests unexpectedly pass, pytest will report as xpass,
        indicating a limitation has been resolved.
        """
        subdirectory, filename = test_file
        test_path = Path(__file__).parent.parent / subdirectory / filename

        if not test_path.exists():
            pytest.skip(f"Test file {subdirectory}/{filename} not found")

        # Execute the Dana file using a fresh sandbox (with shared API server)
        _result = fresh_dana_sandbox.run(str(test_path))
        # If we reach here, the execution succeeded
        # pytest.xfail will automatically handle this as xpass (unexpected pass)
