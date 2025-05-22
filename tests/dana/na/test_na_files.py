"""
Test runner for .na files.

This module provides functionality to run .na files as tests
to ensure they can be successfully parsed and executed.
"""

from pathlib import Path

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import parse_program
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def get_na_files():
    """Return a list of all .na files in the current directory."""
    current_dir = Path(__file__).parent
    return [str(f) for f in current_dir.glob("*.na")]


@pytest.mark.parametrize("na_file", get_na_files())
def test_na_file(na_file):
    """Test that a .na file can be parsed and executed without errors."""
    # Read the .na file
    with open(na_file) as f:
        program_text = f.read()

    # Create a context with necessary resources
    context = SandboxContext()

    # Initialize LLM resource if needed
    if "reason(" in program_text:
        llm_resource = LLMResource()
        context.set("system.llm_resource", llm_resource)

    # Parse the program
    program = parse_program(program_text)
    assert program is not None, f"Failed to parse {na_file}"

    # Initialize interpreter
    interpreter = DanaInterpreter(context)

    # Execute the program
    result = interpreter.execute_program(program)

    # Check that execution completed successfully
    assert result.status.is_success, f"Failed to execute {na_file}: {result.status.message}"

    # Log the result
    print(f"Successfully executed {na_file}")
    print(f"Context after execution: {context.get_all()}")
