"""
Tests for Dana f-string underscore variable fix.

Covers the fix for underscore handling in f-string variable names,
where variables like 'question_2' were incorrectly treated as literals instead of identifiers.

NOTE: These tests are fully independent of OPENAI_API_KEY.
"""

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.ast import Identifier
from dana.core.lang.parser.transformer.fstring_transformer import FStringTransformer
from dana.core.lang.parser.utils.identifier_utils import is_valid_identifier
from dana.core.lang.parser.utils.parsing_utils import ParserCache
from dana.core.lang.sandbox_context import SandboxContext


def test_underscore_variables_in_fstring_parsing():
    """Test the core regression: underscore variables should be parsed as identifiers."""
    transformer = FStringTransformer()

    # This was the bug - question_2 was treated as literal instead of identifier
    result = transformer._parse_expression_term("question_2")
    assert isinstance(result, Identifier)
    assert result.name == "question_2"  # Same as regular expressions - no automatic prefix

    # Test a few more underscore cases
    result = transformer._parse_expression_term("_private")
    assert isinstance(result, Identifier)
    assert result.name == "_private"  # Same as regular expressions - no automatic prefix


def test_underscore_variables_in_fstring_execution():
    """Test the core regression: underscore variables should work in f-string execution."""
    parser = ParserCache.get_parser("dana")
    interpreter = DanaInterpreter()
    context = SandboxContext()

    code = """
question_2 = "What is DANA"
result = f"Question: {question_2}"
"""

    program = parser.parse(code, do_transform=True)
    interpreter.execute_program(program, context)

    result = context.get("local:result")

    # The bug: this would output "Question: question_2"
    # The fix: this should output "Question: What is DANA"
    assert result == "Question: What is DANA"
    assert "question_2" not in result  # Ensure it's not treating variable name as literal


def test_basic_fstring_still_works():
    """Test that basic f-string functionality wasn't broken by the fix."""
    parser = ParserCache.get_parser("dana")
    interpreter = DanaInterpreter()
    context = SandboxContext()

    code = """
name = "Alice"
result = f"Hello {name}"
"""

    program = parser.parse(code, do_transform=True)
    interpreter.execute_program(program, context)

    result = context.get("local:result")
    assert result == "Hello Alice"


def test_original_failing_case():
    """Test the exact case from the original bug report."""
    parser = ParserCache.get_parser("dana")
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Mock the reason function to avoid LLM calls
    def mock_reason(*args, **kwargs):
        return "DANA is a digital wallet"

    interpreter.function_registry.register(name="reason", func=mock_reason, func_type=FunctionType.PYTHON, overwrite=True)

    code = """
question_2 = "What is DANA"
answer = reason(question_2)
result = f"Question : {question_2}. Answer : {answer}"
"""

    program = parser.parse(code, do_transform=True)
    interpreter.execute_program(program, context)

    result = context.get("local:result")

    # Verify the fix works
    assert "What is DANA" in result
    assert "question_2" not in result
    assert "DANA is a digital wallet" in result


def test_common_identifier_utility():
    """Test the common is_valid_identifier utility function."""
    # Valid identifiers
    assert is_valid_identifier("x")
    assert is_valid_identifier("question_2")
    assert is_valid_identifier("_private")
    assert is_valid_identifier("obj.attr")
    assert is_valid_identifier("local:var")
    assert is_valid_identifier("item_123")

    # Invalid identifiers
    assert not is_valid_identifier("123invalid")
    assert not is_valid_identifier("with-dash")
    assert not is_valid_identifier("")
    assert not is_valid_identifier("obj..attr")  # consecutive dots
    assert not is_valid_identifier(".attr")  # leading dot


if __name__ == "__main__":
    pytest.main([__file__])
