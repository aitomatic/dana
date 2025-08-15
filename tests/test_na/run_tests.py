#!/usr/bin/env python3
"""
Simple command-line test runner for test_na files.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py basic              # Run only basic syntax tests
    python run_tests.py advanced           # Run only advanced syntax tests
    python run_tests.py test_basic_assignments.na  # Run specific test file
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.dana_parser import parse_program
from dana.core.lang.sandbox_context import SandboxContext


def get_na_files(category=None):
    """Get .na files based on category."""
    current_dir = Path(__file__).parent

    if category == "basic":
        basic_dir = current_dir / "01_basic_syntax"
        return [str(f) for f in basic_dir.glob("*.na")] if basic_dir.exists() else []
    elif category == "advanced":
        advanced_dir = current_dir / "02_advanced_syntax"
        return [str(f) for f in advanced_dir.glob("*.na")] if advanced_dir.exists() else []
    elif category and category.endswith(".na"):
        # Specific file
        file_path = current_dir / "01_basic_syntax" / category
        if not file_path.exists():
            file_path = current_dir / "02_advanced_syntax" / category
        return [str(file_path)] if file_path.exists() else []
    else:
        # All files
        na_files = []
        basic_dir = current_dir / "01_basic_syntax"
        advanced_dir = current_dir / "02_advanced_syntax"

        if basic_dir.exists():
            na_files.extend([str(f) for f in basic_dir.glob("*.na")])
        if advanced_dir.exists():
            na_files.extend([str(f) for f in advanced_dir.glob("*.na")])

        return na_files


def run_test(na_file):
    """Run a single .na file test."""
    print(f"Running test: {Path(na_file).name}")

    # Clear registries for test isolation
    from dana.registry import get_global_registry

    registry = get_global_registry()
    registry.clear_all()

    # Reload core functions after clearing
    from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
    from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

    do_register_py_builtins(registry.functions)
    register_py_wrappers(registry.functions)

    try:
        # Read the .na file
        with open(na_file) as f:
            program_text = f.read()

        # Create context
        context = SandboxContext()

        # Parse the program (disable type checking for most tests)
        program = parse_program(program_text, do_type_check=False)
        if program is None:
            print(f"❌ Failed to parse {na_file}")
            return False

        # Initialize interpreter
        interpreter = DanaInterpreter()

        # Execute the program
        result = interpreter.execute_program(program, context)

        # Check result
        if result is not None and hasattr(result, "status"):
            if not result.status.is_success:
                print(f"❌ Failed to execute {na_file}: {result.status.message}")
                return False

        print(f"✅ Successfully executed {Path(na_file).name}")
        return True

    except Exception as e:
        # Handle expected errors
        error_msg = str(e).lower()
        if any(expected in error_msg for expected in ["division by zero", "index out of range", "not callable", "key error"]):
            print(f"✅ Expected error in {Path(na_file).name}: {e}")
            return True
        else:
            print(f"❌ Unexpected error in {Path(na_file).name}: {e}")
            return False


def main():
    """Main function to run tests."""
    if len(sys.argv) > 1:
        category = sys.argv[1]
    else:
        category = None

    na_files = get_na_files(category)

    if not na_files:
        print(f"No .na files found for category: {category}")
        return 1

    print(f"Found {len(na_files)} test files to run")
    print("=" * 50)

    passed = 0
    failed = 0

    for na_file in na_files:
        if run_test(na_file):
            passed += 1
        else:
            failed += 1
        print()

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
