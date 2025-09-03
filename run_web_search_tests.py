#!/usr/bin/env python3
"""
Test runner script for web search module tests.

This script runs all the web search related tests and provides a summary.
Run from the project root directory.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run web search module tests."""
    # Web search test files
    test_files = [
        "tests/unit/common/resource/test_web_search_models.py",
        "tests/unit/common/resource/test_web_search_interfaces.py",
        "tests/unit/common/resource/test_web_search_google_service.py",
        "tests/unit/common/resource/test_web_search_llama_service.py",
        "tests/unit/common/resource/test_web_search_utils.py",
        "tests/unit/common/resource/test_web_search_resource.py",
    ]

    print("🚀 Running Web Search Module Tests")
    print("=" * 50)

    # Check if all test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)

    if missing_files:
        print("❌ Missing test files:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    # Run tests
    try:
        # Run pytest with verbose output and coverage
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--durations=10",  # Show slowest 10 tests
            *test_files,
        ]

        print(f"Running command: {' '.join(cmd)}")
        print()

        result = subprocess.run(cmd, capture_output=False)

        if result.returncode == 0:
            print("\n✅ All web search tests passed!")
            return True
        else:
            print(f"\n❌ Tests failed with return code {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main():
    """Main function."""
    print("Web Search Module Test Runner")
    print("This script runs comprehensive tests for the dana web search module.")
    print()

    # Check if we're in the right directory
    if not Path("dana").exists():
        print("❌ Please run this script from the project root directory (where dana/ folder exists)")
        sys.exit(1)

    success = run_tests()

    if success:
        print("\n🎉 Test suite completed successfully!")
        print("\nTest Coverage Summary:")
        print("✅ Core Models (SearchRequest, SearchResults, etc.)")
        print("✅ Protocol Interfaces (SearchService, DomainHandler)")
        print("✅ Google Search Service Implementation")
        print("✅ Llama Search Service Implementation")
        print("✅ Utility Functions (ContentProcessor, Summarizer, LLM)")
        print("✅ Main WebSearchResource Implementation")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
