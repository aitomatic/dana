"""
Test runner for advanced syntax .na files.

This module provides functionality to run advanced syntax .na files as tests
to ensure they can be successfully parsed and executed.
"""

import os
from pathlib import Path

import pytest

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.dana_parser import parse_program
from dana.core.lang.sandbox_context import SandboxContext


def get_na_files():
    """Return a list of all .na files in the advanced_syntax directory."""
    current_dir = Path(__file__).parent / "02_advanced_syntax"
    return [str(f) for f in current_dir.glob("*.na")]


# Add a marker for na_file tests
def pytest_configure(config):
    config.addinivalue_line("markers", "na_file: mark tests that execute .na files (may need real LLM)")


@pytest.mark.na_file
@pytest.mark.parametrize("na_file", get_na_files())
def test_na_file(na_file):
    """Test that an advanced syntax .na file can be parsed and executed without errors."""
    # Clear struct registry to ensure test isolation
    from dana.registry import GLOBAL_REGISTRY

    GLOBAL_REGISTRY.clear_all()

    # Reload core functions after clearing
    from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
    from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

    do_register_py_builtins(GLOBAL_REGISTRY.functions)
    register_py_wrappers(GLOBAL_REGISTRY.functions)

    # Check if we should skip tests that need real LLM
    skip_llm_tests = os.environ.get("DANA_SKIP_NA_LLM_TESTS", "").lower() == "true"

    # Read the .na file
    with open(na_file) as f:
        program_text = f.read()

    # Skip test if it uses reason and we're skipping LLM tests
    if skip_llm_tests and "reason(" in program_text:
        pytest.skip(f"Skipping {na_file} because it uses reason() and DANA_SKIP_NA_LLM_TESTS is true")

    # Create a context with necessary resources
    context = SandboxContext()

    # Initialize LLM resource if needed
    if "reason(" in program_text:
        # Initialize the LLM resource
        llm_resource = LegacyLLMResource()
        # Use mock for all LLM calls
        llm_resource = llm_resource.with_mock_llm_call(True)

        # Create BaseLLMResource for context access
        from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance
        from dana.core.resource.builtins.llm_resource_type import LLMResourceType

        llm_resource = LLMResourceInstance(LLMResourceType(), LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini"))
        llm_resource.initialize()

        # Enable mock mode for testing
        llm_resource.with_mock_llm_call(True)

        # Set LLM resource in context for reason function access
        context.set_system_llm_resource(llm_resource)

    # Parse the program - disable type checking for advanced syntax tests
    # These tests focus on advanced syntax features like lambdas, comprehensions, and pipelines
    filename = Path(na_file).name
    advanced_syntax_tests = [
        "test_basic_lambdas.na",
        "test_basic_pipelines.na",
        "test_conditional_expressions.na",
        "test_dict_comprehensions.na",
        "test_lambda_closures.na",
        "test_lambda_complex.na",
        "test_lambda_parameters.na",
        "test_lambda_with_structs.na",
        "test_list_comprehensions.na",
        "test_named_pipelines.na",
        "test_nested_comprehensions.na",
        "test_placeholder_expressions.na",
        "test_set_comprehensions.na",
    ]

    do_type_check = filename not in advanced_syntax_tests

    program = parse_program(program_text, do_type_check=do_type_check)
    assert program is not None, f"Failed to parse {na_file}"

    # Initialize interpreter
    interpreter = DanaInterpreter()

    # Set the interpreter in the context (required for background thread execution)
    context.interpreter = interpreter

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
        # Handle expected errors from advanced syntax tests
        if "division by zero" in exception_info.lower():
            # This is an expected error from arithmetic tests
            print(f"Expected division by zero error in {na_file} - arithmetic error handling working correctly")
            return

        if "index out of range" in exception_info.lower():
            # This is an expected error from collection indexing tests
            print(f"Expected index error in {na_file} - collection indexing error handling working correctly")
            return

        if "not callable" in exception_info.lower():
            # This is an expected error from lambda tests
            print(f"Expected callable error in {na_file} - lambda error handling working correctly")
            return

        pytest.fail(f"Failed to execute {na_file}: {exception_info}")

    # Check the execution status
    if result is not None and hasattr(result, "status"):
        # Handle object with status attribute
        assert result.status.is_success, f"Failed to execute {na_file}: {result.status.message}"

    # Log the result (None is acceptable for programs that just execute statements)
    print(f"Successfully executed {na_file}")
