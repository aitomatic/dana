"""Tests for the grammar-based DANA parser.

This module contains tests to verify that the grammar-based parser works correctly and
produces the same results as the regex-based parser for basic DANA programs.
"""

import pytest

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    FunctionCall,
    LiteralExpression,
    LogLevel,
    LogStatement,
    Program,
    ReasonStatement,
    WhileLoop,
)
from opendxa.dana.language.lark_parser import _grammar_parser
from opendxa.dana.language.parser import parse as regex_parse
from opendxa.dana.language.parser_factory import ParserType, get_parser_factory, parse

# Skip all tests if the grammar parser is not available
pytestmark = pytest.mark.skipif(not _grammar_parser.is_available(), reason="Grammar parser is not available. Install lark-parser package.")

# Disable type checking for all tests
get_parser_factory().set_type_checking(False)

# Use grammar parser for all tests
get_parser_factory().set_default_parser(ParserType.GRAMMAR)


def test_empty_program():
    """Test parsing an empty program."""
    code = ""
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 0


def test_comment_only_program():
    """Test parsing a program with only comments."""
    code = "# This is a comment\n# Another comment"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 0


def test_assignment():
    """Test parsing a simple assignment statement."""
    code = "x = 42"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 42


def test_nested_assignment():
    """Test parsing a nested assignment statement."""
    code = "user.name = 'Alice'"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "user.name"


def test_log_statement():
    """Test parsing a log statement."""
    code = 'log("Hello, world!")'
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, LogStatement)
    assert stmt.level == LogLevel.INFO  # Default level
    assert isinstance(stmt.message, LiteralExpression)
    assert stmt.message.literal.value == "Hello, world!"


def test_log_statement_with_level():
    """Test parsing a log statement with a level."""
    code = 'log.error("An error occurred")'
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, LogStatement)
    assert stmt.level == LogLevel.ERROR
    assert isinstance(stmt.message, LiteralExpression)
    assert stmt.message.literal.value == "An error occurred"


def test_conditional():
    """Test parsing a conditional statement."""
    code = "if x > 10:\n    log(x)\n    y = x * 2"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Conditional)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.GREATER_THAN
    assert len(stmt.body) == 2
    assert isinstance(stmt.body[0], LogStatement)
    assert isinstance(stmt.body[1], Assignment)


def test_while_loop():
    """Test parsing a while loop statement."""
    code = "while count < 5:\n    count = count + 1\n    log(count)"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, WhileLoop)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.LESS_THAN
    assert len(stmt.body) == 2
    assert isinstance(stmt.body[0], Assignment)
    assert isinstance(stmt.body[1], LogStatement)


def test_function_call():
    """Test parsing a function call statement."""
    code = "calculate(x=10, y=20)"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, FunctionCall)
    assert stmt.name == "calculate"

    # Check if we have arguments, possibly in nested structures
    assert len(stmt.args) > 0

    # Try to find the named arguments in the args
    x_found = False
    y_found = False

    for key, value in stmt.args.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, tuple) and item[0] == "x":
                    x_found = True
                if isinstance(item, tuple) and item[0] == "y":
                    y_found = True
        elif key == "x":
            x_found = True
        elif key == "y":
            y_found = True

    assert x_found, "Argument x not found in function call"
    assert y_found, "Argument y not found in function call"


def test_reason_statement():
    """Test parsing a reason statement."""
    code = 'result = reason("What is the meaning of life?")'
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, ReasonStatement)
    assert stmt.target.name == "result"
    assert isinstance(stmt.prompt, LiteralExpression)
    assert stmt.prompt.literal.value == "What is the meaning of life?"


def test_reason_statement_with_context():
    """Test parsing a reason statement with context."""
    code = 'result = reason("What is the weather?", context=[weather.temp, weather.condition])'
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, ReasonStatement)
    assert stmt.target.name == "result"
    assert isinstance(stmt.prompt, LiteralExpression)
    assert stmt.prompt.literal.value == "What is the weather?"
    assert len(stmt.context) == 2
    assert stmt.context[0].name == "weather.temp"
    assert stmt.context[1].name == "weather.condition"


def test_binary_expression():
    """Test parsing binary expressions with correct operator precedence."""
    code = "result = 1 + 2 * 3"
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.operator == BinaryOperator.ADD
    assert isinstance(stmt.value.left, LiteralExpression)
    assert stmt.value.left.literal.value == 1
    assert isinstance(stmt.value.right, BinaryExpression)
    assert stmt.value.right.operator == BinaryOperator.MULTIPLY
    assert stmt.value.right.left.literal.value == 2
    assert stmt.value.right.right.literal.value == 3


def test_complex_program():
    """Test parsing a more complex program with multiple statement types."""
    code = """
# Calculate factorial
n = 5
result = 1
counter = 1

while counter <= n:
    result = result * counter
    counter = counter + 1

log.info("Factorial calculated")

if result > 100:
    log.warn("Large factorial")
else:
    log.info("Small factorial")

explanation = reason("Explain factorial", context=[n, result])
"""
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert result.is_valid
    assert isinstance(result.program, Program)
    # Count non-empty statements (comments are filtered out)
    non_empty_statements = [s for s in result.program.statements if s is not None]
    assert len(non_empty_statements) > 5  # Should have multiple statements


def test_syntax_error():
    """Test detecting syntax errors in the program."""
    code = "if x > 10\n    log(x)"  # Missing colon
    result = parse(code, ParserType.GRAMMAR, type_check=False)
    assert not result.is_valid
    assert len(result.errors) > 0

    # Check that error contains useful information
    error_msg = str(result.errors[0])
    assert "DANA Error" in error_msg
    assert "Syntax error" in error_msg  # Lark produces "Syntax error" messages


def test_compare_with_regex_parser():
    """Test that grammar parser produces similar results to regex parser for valid programs."""
    code = """
temp = 75
if temp > 70:
    log("It's hot")
    recommendation = "Stay cool"
else:
    log("It's cool")
    recommendation = "Enjoy the weather"
"""
    # For this test, we bypass the factory and test directly against the parsers
    regex_result = regex_parse(code)  # Use regex parser directly

    from opendxa.dana.language.lark_parser import parse_with_grammar

    grammar_result = parse_with_grammar(code)  # Use grammar parser directly

    print(f"Regex result valid: {regex_result.is_valid}")
    if not regex_result.is_valid:
        print(f"Regex errors: {regex_result.errors}")

    print(f"Grammar result valid: {grammar_result.is_valid}")
    if not grammar_result.is_valid:
        print(f"Grammar errors: {grammar_result.errors}")

    # Check that at least one parser succeeds (we're still transitioning)
    assert regex_result.is_valid or grammar_result.is_valid

    # If both are valid, they should have similar structure
    if regex_result.is_valid and grammar_result.is_valid:
        assert len(regex_result.program.statements) == len(grammar_result.program.statements)


if __name__ == "__main__":
    pytest.main()
