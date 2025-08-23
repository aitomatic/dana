"""
Test runner for .na files.

This module provides functionality to run .na files as tests
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
    # Clear struct registry to ensure test isolation
    from dana.registry import GLOBAL_REGISTRY

    GLOBAL_REGISTRY.types.clear()

    # Check if we should skip tests that need real LLM
    skip_llm_tests = os.environ.get("DANA_SKIP_NA_LLM_TESTS", "").lower() == "true"

    # Note: test_simple.na now uses correct private.result syntax

    # Read the .na file
    with open(na_file) as f:
        program_text = f.read()

    # Skip test if it uses reason and we're skipping LLM tests
    if skip_llm_tests and "reason(" in program_text:
        pytest.skip(f"Skipping {na_file} because it uses reason() and DANA_SKIP_NA_LLM_TESTS is true")

    # Create a context with necessary resources
    context = SandboxContext()

    # Clear registries to ensure test isolation
    from dana.registry import GLOBAL_REGISTRY

    GLOBAL_REGISTRY.clear_all()

    # Reload core functions after clearing
    from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
    from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

    do_register_py_builtins(GLOBAL_REGISTRY.functions)
    register_py_wrappers(GLOBAL_REGISTRY.functions)

    # Initialize LLM resource if needed
    if "reason(" in program_text:
        # Initialize the LLM resource
        llm_resource = LegacyLLMResource()
        # Use mock for all LLM calls
        llm_resource = llm_resource.with_mock_llm_call(True)

        # Create BaseLLMResource for context access
        from dana.builtin_types.resource.builtins.llm_resource_instance import LLMResourceInstance
        from dana.builtin_types.resource.builtins.llm_resource_type import LLMResourceType

        llm_resource = LLMResourceInstance(LLMResourceType(), LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini"))
        llm_resource.initialize()

        # Enable mock mode for testing
        # LLMResourceInstance wraps LegacyLLMResource directly, no bridge needed
        llm_resource.with_mock_llm_call(True)

        # Set LLM resource in context for reason function access
        context.set_system_llm_resource(llm_resource)

    # Parse the program - disable type checking for enhanced coercion tests
    # These tests specifically test runtime coercion that TypeChecker doesn't understand
    filename = Path(na_file).name
    enhanced_coercion_tests = [
        "test_enhanced_coercion_basic.na",
        "test_enhanced_coercion_comprehensive.na",
        "test_coercion_regression_prevention.na",
        "test_poet_enhanced_function_dispatch.na",
        "test_method_chaining_builtin.na",
        "test_method_chaining_user_defined.na",
        "test_method_chaining_integration.na",
        "test_method_chaining_edge_cases.na",
        "test_nested_conditionals_with_structs.na",
        "test_compound_assignments.na",  # Temporarily disable type checking for compound assignments
        "test_phase1_parser.na",  # Disable type checking for struct method tests
        "test_phase2_registry.na",  # Disable type checking for struct method tests
        "test_agent_keyword.na",  # Disable type checking for agent tests
        "test_dict_comprehensions.na",  # Disable type checking for dict comprehensions (type checker scoping issue)
        "test_lambda_collections.na",  # Disable type checking for lambda collections (type checker scoping issue)
        "test_list_comprehensions.na",  # Disable type checking for list comprehensions (type checker scoping issue)
        "test_lambda_expressions.na",  # Disable type checking for lambda expressions (type checker unsupported expression)
        "test_set_comprehensions.na",  # Disable type checking for set comprehensions (type checker for loop issue)
        "test_lambda_struct_receivers.na",  # Disable type checking for lambda struct receivers (type checker scoping issue)
        "test_interface_basic.na",  # Disable type checking for interface tests
        "test_interface_validation.na",  # Disable type checking for interface tests
        "test_interface_integration.na",  # Disable type checking for interface tests
    ]
    disable_type_check = filename in enhanced_coercion_tests

    program = parse_program(program_text, do_type_check=not disable_type_check)
    assert program is not None, f"Failed to parse {na_file}"

    # Initialize interpreter first (so real functions get registered)
    interpreter = DanaInterpreter()

    # No longer overriding DANA_MOCK_LLM - let environment control it
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
        pytest.fail(f"Failed to execute {na_file}: {exception_info}")

    # Check the execution status
    if result is not None and hasattr(result, "status"):
        # Handle object with status attribute
        assert result.status.is_success, f"Failed to execute {na_file}: {result.status.message}"

    # Log the result (None is acceptable for programs that just execute statements)
    print(f"Successfully executed {na_file}")
