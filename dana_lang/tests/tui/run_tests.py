#!/usr/bin/env python3
"""
Test runner for Dana TUI tests.

This script provides an easy way to run TUI tests with different configurations.
Supports all test types: unit, UI, integration, snapshot, and performance tests.

Usage:
    python tests/tui/run_tests.py [options]

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description=""):
    """Run a command and print the result."""
    if description:
        print(f"\n🧪 {description}")
        print("=" * 50)

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        print("✅ Success")
    else:
        print("❌ Failed")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Run Dana TUI tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage")
    parser.add_argument("--fast", "-f", action="store_true", help="Skip slow tests")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--test", help="Run specific test method")
    parser.add_argument("--marker", "-m", help="Run tests with specific marker")
    parser.add_argument("--keyword", "-k", help="Run tests matching keyword")
    parser.add_argument(
        "--type", choices=["unit", "ui", "integration", "snapshot", "performance", "all"], default="all", help="Test type to run"
    )
    parser.add_argument("--update-snapshots", action="store_true", help="Update snapshot tests")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (requires pytest-xdist)")

    args = parser.parse_args()

    # Check if pytest is available
    try:
        subprocess.run(["python", "-m", "pytest", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest not found. Install with: pip install pytest pytest-asyncio")
        return 1

    # Build pytest command
    cmd = ["python", "-m", "pytest", "tests/tui/"]

    if args.verbose:
        cmd.append("-v")

    if args.coverage:
        cmd.extend(["--cov=dana.apps.tui", "--cov-report=term-missing", "--cov-report=html"])

    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Handle test type selection
    if args.type != "all":
        if args.type == "unit":
            cmd.extend(["-m", "unit"])
        elif args.type == "ui":
            cmd.extend(["-m", "ui"])
        elif args.type == "integration":
            cmd.extend(["-m", "integration"])
        elif args.type == "snapshot":
            cmd.extend(["-m", "snapshot"])
        elif args.type == "performance":
            cmd.extend(["-m", "performance"])
    elif args.fast:
        cmd.extend(["-m", "not slow"])
    elif args.marker:
        cmd.extend(["-m", args.marker])

    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # Handle snapshot updates
    if args.update_snapshots:
        cmd.append("--snapshot-update")

    # Handle specific file or test
    if args.file:
        cmd[-1] = f"tests/tui/{args.file}"
        if not args.file.endswith(".py"):
            cmd[-1] += ".py"

    if args.test:
        if "::" not in args.test:
            print("❌ Test format should be: filename.py::TestClass::test_method")
            return 1
        cmd[-1] = f"tests/tui/{args.test}"

    # Run the tests
    test_type_desc = f"Running Dana TUI {args.type.title()} Tests"
    success = run_command(cmd, test_type_desc)

    if success and args.coverage:
        print("\n📊 Coverage report generated in htmlcov/index.html")

    return 0 if success else 1


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")

    deps = {
        "pytest": "pytest",
        "pytest-asyncio": "pytest_asyncio",
        "textual": "textual",
        "pytest-textual-snapshot": "pytest_textual_snapshot",
    }

    missing = []
    optional = []

    for name, module in deps.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            if name in ["textual", "pytest-textual-snapshot"]:
                print(f"⚠️  {name} (optional - needed for UI/snapshot tests)")
                optional.append(name)
            else:
                print(f"❌ {name}")
                missing.append(name)

    if missing:
        print("\n📦 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False

    if optional:
        print("\n📦 Optional dependencies for full testing:")
        print(f"pip install {' '.join(optional)}")

    return True


def show_test_summary():
    """Show summary of available tests."""
    print("\n📋 Available Test Files:")
    print("  test_runtime.py           - Core runtime components")
    print("  test_runtime_improved.py  - Enhanced unit tests")
    print("  test_taskman.py           - Task management")
    print("  test_router.py            - Command parsing and routing")
    print("  test_ui_components.py     - UI component tests")
    print("  test_integration.py       - Integration tests")
    print("  test_snapshots.py         - Visual regression tests")
    print("  test_performance.py       - Performance benchmarks")

    print("\n🏷️  Test Markers:")
    print("  unit         - Unit tests (core logic)")
    print("  ui           - UI component tests")
    print("  integration  - Integration tests")
    print("  snapshot     - Snapshot tests")
    print("  performance  - Performance tests")
    print("  slow         - Slow-running tests")

    print("\n🏃 Quick Commands:")
    print("  python tests/tui/run_tests.py                    # Run all tests")
    print("  python tests/tui/run_tests.py --type unit        # Run unit tests only")
    print("  python tests/tui/run_tests.py --type ui          # Run UI tests only")
    print("  python tests/tui/run_tests.py --type integration # Run integration tests")
    print("  python tests/tui/run_tests.py --type snapshot    # Run snapshot tests")
    print("  python tests/tui/run_tests.py --type performance # Run performance tests")
    print("  python tests/tui/run_tests.py -v                 # Verbose output")
    print("  python tests/tui/run_tests.py -c                 # With coverage")
    print("  python tests/tui/run_tests.py --fast             # Skip slow tests")
    print("  python tests/tui/run_tests.py --update-snapshots # Update snapshots")
    print("  python tests/tui/run_tests.py --file test_ui_components # Run specific file")
    print("  python tests/tui/run_tests.py -k cancel          # Run cancel tests")


def show_test_types():
    """Show detailed information about test types."""
    print("\n📚 Test Type Details:")

    print("\n🔧 Unit Tests (--type unit):")
    print("  - Test individual components in isolation")
    print("  - Fast execution (< 1 second per test)")
    print("  - Mock external dependencies")
    print("  - Focus on core logic and edge cases")

    print("\n🖥️  UI Tests (--type ui):")
    print("  - Test user interactions using Textual Pilot")
    print("  - Simulate real user behavior")
    print("  - Test widget functionality")
    print("  - Requires textual dependency")

    print("\n🔗 Integration Tests (--type integration):")
    print("  - Test complete workflows")
    print("  - End-to-end user scenarios")
    print("  - Test component interactions")
    print("  - Slower execution (2-5 seconds per test)")

    print("\n📸 Snapshot Tests (--type snapshot):")
    print("  - Visual regression testing")
    print("  - Catch UI appearance changes")
    print("  - Generate HTML reports")
    print("  - Requires pytest-textual-snapshot")

    print("\n⚡ Performance Tests (--type performance):")
    print("  - Test UI responsiveness")
    print("  - Benchmark execution times")
    print("  - Test scalability")
    print("  - Marked as slow tests")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        show_test_summary()
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--check-deps":
        check_dependencies()
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--test-types":
        show_test_types()
        sys.exit(0)

    sys.exit(main())
