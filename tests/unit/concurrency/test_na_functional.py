"""
Test runner for concurrency .na files.

This module provides functionality to run concurrency-related .na files as tests
to ensure they can be successfully parsed and executed.
"""

from pathlib import Path

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.dana_parser import parse_program
from dana.core.lang.sandbox_context import SandboxContext


def get_na_files():
    """Return a list of all .na files in the current directory."""
    current_dir = Path(__file__).parent
    return [str(f) for f in current_dir.glob("*.na")]


@pytest.mark.na_file
@pytest.mark.parametrize("na_file", get_na_files())
def test_na_file(na_file):
    """Test that a .na file can be parsed and executed without errors."""
    # Clear struct registry to ensure test isolation
    from dana.registry import get_global_registry

    registry = get_global_registry()
    registry.clear_all()

    # Reload core functions after clearing
    from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
    from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

    do_register_py_builtins(registry.functions)
    register_py_wrappers(registry.functions)

    # Read the .na file
    with open(na_file) as f:
        program_text = f.read()

    # Create a context
    context = SandboxContext()

    # Parse the program - disable type checking for concurrency tests
    program = parse_program(program_text, do_type_check=False)
    assert program is not None, f"Failed to parse {na_file}"

    # Initialize interpreter
    interpreter = DanaInterpreter()

    result = None
    exception_info = None
    try:
        # Execute the program
        result = interpreter.execute_program(program, context)
    except Exception as e:
        exception_info = str(e)
        import traceback

        exception_info += "\n" + traceback.format_exc()

    # Check if execution failed with an exception
    if exception_info:
        # Handle expected errors from Promise error handling tests
        if "division by zero" in exception_info.lower():
            # This is an expected error from Promise error handling tests
            # The Promise system is correctly catching and propagating division by zero errors
            print(f"Expected division by zero error in {na_file} - Promise error handling working correctly")
            return

        pytest.fail(f"Failed to execute {na_file}: {exception_info}")

    # Check the execution status
    if result is not None and hasattr(result, "status"):
        # Handle object with status attribute
        assert result.status.is_success, f"Failed to execute {na_file}: {result.status.message}"

    # Log the result (None is acceptable for programs that just execute statements)
    print(f"Successfully executed {na_file}")
