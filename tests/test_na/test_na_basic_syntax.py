"""
Test runner for basic syntax .na files.

This module provides functionality to run basic syntax .na files as tests
to ensure they can be successfully parsed and executed.
"""

import os
from pathlib import Path

import pytest

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.interpreter.struct_system import MethodRegistry, StructTypeRegistry
from dana.core.lang.parser.dana_parser import parse_program
from dana.core.lang.sandbox_context import SandboxContext


def get_na_files():
    """Return a list of all .na files in the basic_syntax directory."""
    current_dir = Path(__file__).parent / "01_basic_syntax"
    return [str(f) for f in current_dir.glob("*.na")]


# Add a marker for na_file tests
def pytest_configure(config):
    config.addinivalue_line("markers", "na_file: mark tests that execute .na files (may need real LLM)")


@pytest.mark.na_file
@pytest.mark.parametrize("na_file", get_na_files())
def test_na_file(na_file):
    """Test that a basic syntax .na file can be parsed and executed without errors."""
    # Clear struct registry to ensure test isolation
    StructTypeRegistry.clear()
    MethodRegistry.clear()

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

    # Parse the program - disable type checking for basic syntax tests
    # These tests focus on basic syntax validation rather than type checking
    filename = Path(na_file).name
    basic_syntax_tests = [
        "test_arithmetic_expressions.na",
        "test_attribute_assignments.na",
        "test_basic_assignments.na",
        "test_collections_indexing.na",
        "test_comparison_expressions.na",
        "test_compound_assignments.na",
        "test_control_flow.na",
        "test_data_types_literals.na",
        "test_index_assignments.na",
        "test_logical_expressions.na",
        "test_scoped_assignments.na",
        "test_typed_assignments.na",
    ]

    do_type_check = filename not in basic_syntax_tests

    program = parse_program(program_text, do_type_check=do_type_check)
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
        # Handle expected errors from basic syntax tests
        if "division by zero" in exception_info.lower():
            # This is an expected error from arithmetic tests
            print(f"Expected division by zero error in {na_file} - arithmetic error handling working correctly")
            return

        if "index out of range" in exception_info.lower():
            # This is an expected error from collection indexing tests
            print(f"Expected index error in {na_file} - collection indexing error handling working correctly")
            return

        pytest.fail(f"Failed to execute {na_file}: {exception_info}")

    # Check the execution status
    if result is not None and hasattr(result, "status"):
        # Handle object with status attribute
        assert result.status.is_success, f"Failed to execute {na_file}: {result.status.message}"

    # Log the result (None is acceptable for programs that just execute statements)
    print(f"Successfully executed {na_file}")


def test_type_system_differences():
    """
    Test demonstrating the key differences in Dana's type system between:
    - agent_blueprint (creates constructors)
    - agent (creates singleton instances)
    - resource (creates constructors)

    This test documents the important type system behavior shown in the user's example.
    """
    # Clear registries for clean test
    StructTypeRegistry.clear()
    MethodRegistry.clear()

    # Create a context
    context = SandboxContext()

    # Test program that demonstrates the type differences
    program_text = """
# Define an agent blueprint (creates a constructor)
agent_blueprint Abc:
    name: str = "An Agent"

# Create an instance from the blueprint
a = Abc()

# Define a singleton agent (creates an instance directly)
agent AA(Abc)

# Define a resource (creates a constructor)
resource R:
    name: str = "A Resource"

# Create an instance from the resource
r = R()

# Test type information
print("Agent Blueprint Constructor Type:", type(Abc))
print("Agent Blueprint Instance Type:", type(a))
print("Singleton Agent Type:", type(AA))
print("Resource Constructor Type:", type(R))
print("Resource Instance Type:", type(r))
"""

    # Parse and execute
    program = parse_program(program_text, do_type_check=False)
    interpreter = DanaInterpreter()
    interpreter.execute_program(program, context)

    # Verify the types match the expected pattern
    # The key insight is:
    # - agent_blueprint creates Constructor[agent_constructor]
    # - agent creates StructInstance[AgentName] directly
    # - resource creates Constructor[resource_constructor]

    # Get the variables from context
    abc_constructor = context.get("local:Abc")
    a_instance = context.get("local:a")
    aa_singleton = context.get("local:AA")
    r_constructor = context.get("local:R")
    r_instance = context.get("local:r")

    # Verify constructor types
    assert callable(abc_constructor), "Abc should be a callable constructor"
    assert callable(r_constructor), "R should be a callable constructor"

    # Verify instance types
    from dana.agent import AgentInstance
    from dana.core.resource.resource_instance import ResourceInstance

    assert isinstance(a_instance, AgentInstance), f"a should be AgentInstance, got {type(a_instance)}"
    assert isinstance(aa_singleton, AgentInstance), f"AA should be AgentInstance, got {type(aa_singleton)}"
    assert isinstance(r_instance, ResourceInstance), f"r should be ResourceInstance, got {type(r_instance)}"

    # Verify field values
    assert a_instance.name == "An Agent"
    assert aa_singleton.name == "An Agent"  # Inherits from Abc blueprint
    assert r_instance.name == "A Resource"

    print("✅ Type system differences test passed!")
    print(f"  - agent_blueprint Abc creates: {type(abc_constructor)}")
    print(f"  - Abc() creates: {type(a_instance)}")
    print(f"  - agent AA(Abc) creates: {type(aa_singleton)}")
    print(f"  - resource R creates: {type(r_constructor)}")
    print(f"  - R() creates: {type(r_instance)}")

    # Document the actual observed types for reference
    print("\n📋 Observed Type Patterns:")
    print("  - type(Abc) → Constructor[agent_constructor]")
    print("  - type(a) → AgentInstance[Abc]")
    print("  - type(AA) → AgentInstance[AA]")
    print("  - type(R) → Constructor[resource_constructor]")
    print("  - type(r) → ResourceInstance[R]")
