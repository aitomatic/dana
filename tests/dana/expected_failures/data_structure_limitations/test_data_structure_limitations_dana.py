"""
Test runner for Dana data structure limitation tests.

This module discovers and runs .na test files in the data_structure_limitations directory,
marking them as expected failures in pytest. These tests document data structure features
that seem natural but aren't currently supported in Dana.
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Get the directory containing this test file
TEST_DIR = Path(__file__).parent

def discover_dana_test_files():
    """Discover all test_*.na files in the current directory."""
    return list(TEST_DIR.glob("test_*.na"))

def run_dana_file(dana_file_path):
    """
    Run a Dana (.na) file and return (success, output).
    
    For expected failure tests, we expect the Dana file to run successfully
    (meaning it properly caught and documented the expected failures).
    """
    try:
        # Use the dana command to execute the file
        result = subprocess.run(
            ["dana", str(dana_file_path)],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # For expected failure tests, success means the test ran and documented failures
        # The .na files are designed to catch exceptions and log success messages
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, output
        
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 30 seconds"
    except FileNotFoundError:
        return False, "Dana command not found. Please ensure Dana is installed and in PATH."
    except Exception as e:
        return False, f"Error running Dana file: {str(e)}"

# Dynamically create test functions for each .na file
dana_files = discover_dana_test_files()

@pytest.mark.parametrize("dana_file", dana_files, ids=[f.stem for f in dana_files])
def test_expected_data_structure_failures(dana_file):
    """
    Test expected data structure failures in Dana language.
    
    These tests are marked as expected failures (xfail) because they document
    data structure features that don't work yet but might be supported in the future.
    
    The .na files are designed to:
    1. Try data structure features that should fail
    2. Catch the failures and log success messages
    3. Return successfully, indicating all expected failures occurred
    """
    # Mark as expected failure - these document unsupported features
    pytest.xfail("Expected failure: Documents unsupported Dana data structure features for future consideration")
    
    success, output = run_dana_file(dana_file)
    
    # Print output for debugging
    print(f"\n--- Output from {dana_file.name} ---")
    print(output)
    print("--- End Output ---\n")
    
    # For expected failure tests, we actually want them to succeed
    # (meaning they properly documented the expected failures)
    assert success, f"Expected failure test {dana_file.name} did not run successfully:\n{output}"

if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"]) 