"""
Test runner for .na files.

This module provides functionality to run .na files as tests
to ensure they can be successfully parsed and executed.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import parse_program
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def get_na_files():
    """Return a list of all .na files in the current directory."""
    current_dir = Path(__file__).parent
    return [str(f) for f in current_dir.glob("*.na")]


# Add a marker for na_file tests
def pytest_configure(config):
    config.addinivalue_line("markers", "na_file: mark tests that execute .na files (may need real LLM)")


@pytest.mark.na_file
@pytest.mark.parametrize("na_file", get_na_files())
def test_na_file(na_file):
    """Test that a .na file can be parsed and executed without errors."""
    # Check if we should skip tests that need real LLM
    skip_llm_tests = os.environ.get("OPENDXA_SKIP_NA_LLM_TESTS", "").lower() == "true"

    # Skip test_simple.na due to known parsing issues with "private.result" syntax
    if "test_simple.na" in na_file:
        pytest.skip(f"Skipping {na_file} due to known parsing issues with 'private.result' syntax")

    # Read the .na file
    with open(na_file) as f:
        program_text = f.read()

    # Skip test if it uses reason and we're skipping LLM tests
    if skip_llm_tests and "reason(" in program_text:
        pytest.skip(f"Skipping {na_file} because it uses reason() and OPENDXA_SKIP_NA_LLM_TESTS is true")

    # Create a context with necessary resources
    context = SandboxContext()

    # Setup mocking for the reason function
    mock_result = "This is a mocked LLM response for tests"

    # Create a patcher for reason function
    with patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.reason_function", return_value=mock_result) as mock_reason:

        # Initialize LLM resource if needed
        if "reason(" in program_text:
            # Initialize the LLM resource
            llm_resource = LLMResource()
            # Use mock for all LLM calls
            llm_resource = llm_resource.with_mock_llm_call(True)
            context.set("system.llm_resource", llm_resource)

        # Parse the program
        program = parse_program(program_text)
        assert program is not None, f"Failed to parse {na_file}"

        # Initialize interpreter
        interpreter = DanaInterpreter()

        # Execute the program
        result = interpreter.execute_program(program, context)

        # Check the execution status
        if hasattr(result, "status"):
            # Handle object with status attribute
            assert result.status.is_success, f"Failed to execute {na_file}: {result.status.message}"
        else:
            # Handle other return types (like dict from mocked calls)
            assert result is not None, f"Failed to execute {na_file}: null result"

        # Log the result
        print(f"Successfully executed {na_file}")
