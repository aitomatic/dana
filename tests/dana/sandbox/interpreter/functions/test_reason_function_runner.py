"""
Runner for Dana reason function tests.

This script runs the Dana test files for the reason function.
"""

import os
from pathlib import Path

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def run_test_file(file_path: str | Path) -> None:
    """Run a Dana test file and print its output."""
    sandbox = DanaSandbox(debug=True)
    result = sandbox.run(file_path)
    print(f"\nResults for {file_path}:")
    print(f"Success: {result.success}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"Output: {result.output}")
    print("-" * 80)


def main():
    """Run all Dana test files."""
    # Set mock LLM environment variable
    os.environ["OPENDXA_MOCK_LLM"] = "true"

    # Get the test files directory
    test_files_dir = Path("examples/dana/debug_tests")

    # Run each test file
    test_files = [
        test_files_dir / "test_reason_model_selection.na",
        test_files_dir / "test_reason_model_caching.na",
    ]

    for test_file in test_files:
        run_test_file(test_file)


if __name__ == "__main__":
    main()
