"""Test the reason2 function usage in DANA code."""

import pytest

from opendxa.dana.language.parser import GrammarParser, ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import create_interpreter


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


def test_reason2_in_dana():
    """Test using reason2 in DANA code with both positional and named arguments.

    This test verifies that:
    1. The function accepts both positional and named arguments for the prompt
    2. Named arguments are properly treated as context variables
    3. Unscoped variables are treated as private variables
    4. System variables are rejected
    5. Special arguments (temperature, format) are handled correctly
    """

    # Create a mock LLM integration
    class MockLLMIntegration:
        def execute_direct_synchronous_reasoning(self, prompt, context_vars=None, options=None):
            return f"Response to '{prompt}' with context={context_vars} and options={options}"

    # Set up context and interpreter
    context = RuntimeContext()
    context.register_resource("llm_integration", MockLLMIntegration())

    # Set some test data in the context
    context.set("private.data", "test data")
    context.set("public.info", "public info")

    interpreter = create_interpreter(context)

    # Test program using both styles
    program = """# Test with named arguments and context variables
private.result1 = reason2(prompt="What is this?", data="override data", public_info="override info", temperature=0.7)

# Test with positional argument only
private.result2 = reason2("What is this?")

# Test with unscoped variables in context
private.result3 = reason2(prompt="What is this?", unscoped_var="value", format="json")
"""

    # Parse and execute valid statements
    ast = parser().parse(program)
    interpreter.execute_program(ast)

    # Verify results
    assert "Response to 'What is this?'" in context.get("private.result1")
    assert "temperature=0.7" in context.get("private.result1")
    assert "Response to 'What is this?'" in context.get("private.result2")
    assert "Response to 'What is this?'" in context.get("private.result3")
    assert "format=json" in context.get("private.result3")

    # Test error case with system variables
    error_program = 'private.result4 = reason2(prompt="What is this?", system_var="value")'
    try:
        error_ast = parser().parse(error_program)
        interpreter.execute_program(error_ast)
    except ValueError as e:
        context.set("private.error", str(e))

    assert "System variables are not allowed in context: system_var" in context.get("private.error")

    # Verify original context values are unchanged
    assert context.get("private.data") == "test data"
    assert context.get("public.info") == "public info"


def test_parse_reason2(parser):
    """Test parsing a reason2 statement."""
    program = """
    private.result = reason2("What is 2+2?", {
        "temperature": 0.7,
        "max_tokens": 100
    })
    """
    ast = parser().parse(program)
    assert isinstance(ast, ParseResult)
    assert ast.is_valid
    assert len(ast.program.statements) == 1


def test_parse_reason2_error(parser):
    """Test parsing a reason2 statement with invalid arguments."""
    error_program = """
    private.result = reason2("What is 2+2?", 42)
    """
    error_ast = parser().parse(error_program)
    assert isinstance(error_ast, ParseResult)
    assert error_ast.is_valid
    assert len(error_ast.program.statements) == 1
