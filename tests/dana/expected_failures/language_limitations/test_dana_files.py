"""
Test runner for language limitation .na files using pytest.

This test runner automatically discovers and executes test_*.na files in the
tests/dana/expected_failures/language_limitations/ directory, marking them as expected
failures to document known Dana language limitations.
"""

import pytest
from pathlib import Path
from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


# Test files that are expected to fail due to language limitations
EXPECTED_FAILURE_FILES = [
    "test_expected_syntax_failures.na",
    "test_expected_data_structure_failures.na", 
    "test_expected_function_failures.na",
    "test_expected_operator_failures.na",
    "test_expected_fstring_limitations.na",  # F-string expression limitations
]


class TestDanaLanguageLimitations:
    """Test suite for Dana language limitations documented in .na files."""

    @pytest.mark.parametrize("test_file", EXPECTED_FAILURE_FILES)
    @pytest.mark.xfail(reason="Expected language limitation - documents current Dana parser constraints")
    def test_expected_failures(self, test_file):
        """
        Execute expected failure .na files to document language limitations.
        
        These tests are marked as expected failures (xfail) to:
        1. Document current Dana language limitations
        2. Track which features need implementation
        3. Provide regression tests for future improvements
        4. Pass CI/CD while documenting gaps
        """
        test_path = Path(__file__).parent / test_file
        
        if not test_path.exists():
            pytest.skip(f"Test file {test_file} not found")
        
        # Execute the Dana file - these are expected to demonstrate limitations
        with DanaSandbox() as sandbox:
            try:
                result = sandbox.execute_file(str(test_path))
                # If execution succeeds, the limitations may have been resolved
                assert result is not None, f"Expected failure test {test_file} executed successfully"
            except Exception as e:
                # Expected - these tests document current limitations
                pytest.fail(f"Expected failure in {test_file}: {str(e)}") 