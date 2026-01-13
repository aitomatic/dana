"""
Pytest-compatible test suite that runs all package tests.

This module contains pytest tests that run the test suites for each
package (dana_agent, dana_lang, dana_studio) as subprocess calls.

Usage:
    pytest tests/test_all_packages.py           # Run all package tests
    pytest tests/test_all_packages.py -v        # Verbose
    pytest tests/test_all_packages.py -k agent  # Run only dana_agent tests
"""

import subprocess
import sys
from pathlib import Path

import pytest


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent.resolve()


def run_package_tests(package_dir: str, extra_args: list[str] = None) -> int:
    """
    Run pytest for a package in its directory.

    Args:
        package_dir: Name of the package directory
        extra_args: Additional arguments to pass to pytest

    Returns:
        Exit code from pytest (0 = success)
    """
    repo_root = get_repo_root()
    pkg_path = repo_root / package_dir

    if not (pkg_path / "tests").exists():
        pytest.skip(f"No tests directory found in {package_dir}")

    # Build command
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    if extra_args:
        cmd.extend(extra_args)

    # Run pytest
    result = subprocess.run(
        cmd,
        cwd=str(pkg_path),
        capture_output=False,  # Show output in real-time
        env={
            **subprocess.os.environ,
            "DANA_MOCK_LLM": "true",
            "DANA_USE_REAL_LLM": "false",
        },
    )

    return result.returncode


class TestDanaAgent:
    """Test suite for dana_agent package."""

    def test_dana_agent_suite(self):
        """Run the full dana_agent test suite."""
        exit_code = run_package_tests("dana_agent", ["--maxfail=10"])
        assert exit_code == 0, "dana_agent tests failed"


class TestDanaLang:
    """Test suite for dana_lang package."""

    def test_dana_lang_suite(self):
        """Run the full dana_lang test suite."""
        exit_code = run_package_tests("dana_lang", ["--maxfail=10"])
        assert exit_code == 0, "dana_lang tests failed"


class TestDanaStudio:
    """Test suite for dana_studio package."""

    def test_dana_studio_suite(self):
        """Run the full dana_studio test suite."""
        exit_code = run_package_tests("dana_studio", ["--maxfail=10"])
        assert exit_code == 0, "dana_studio tests failed"


# Mark these as integration tests since they run full test suites
pytestmark = pytest.mark.integration


if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])
