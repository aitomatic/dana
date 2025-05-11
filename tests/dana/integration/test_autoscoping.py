"""Tests for DANA's autoscoping behavior."""

import pytest

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    FStringExpression,
    Identifier,
)
from opendxa.dana.language.parser import GrammarParser, ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import create_interpreter


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


@pytest.fixture
def context():
    """Create a runtime context for testing."""
    return RuntimeContext()


def test_implicit_private_scope(parser):
    """Test that variables without scope prefix are treated as private."""
    # Test simple assignment
    result = parser.parse("x = 42", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.x"

    # Test nested assignment
    result = parser.parse("user.profile.name = 'John'", type_check=False)
    assert not result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.user.profile.name"


def test_explicit_scope_preservation(parser):
    """Test that explicit scope prefixes are preserved."""
    # Test public scope
    result = parser.parse("public.x = 42", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "public.x"

    # Test system scope
    result = parser.parse("system.config.value = true", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "system.config.value"


def test_binary_expressions(parser):
    """Test autoscoping in binary expressions."""
    # Test simple binary expression
    result = parser.parse("y = x + 10", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.y"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "local.x"

    # Test complex binary expression
    result = parser.parse("result = a + b * c", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.result"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "local.a"
    assert stmt.value.right.left.name == "local.b"
    assert stmt.value.right.right.name == "local.c"


def test_mixed_scope_expressions(parser):
    """Test expressions mixing implicit and explicit scopes."""
    # Test mixed scope binary expression
    result = parser.parse("y = x + public.value", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.y"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "local.x"
    assert stmt.value.right.name == "public.value"

    # Test nested mixed scope
    result = parser.parse("result = user.profile.name + system.config.value", type_check=False)
    assert not result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.result"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "local.user.profile.name"
    assert stmt.value.right.name == "system.config.value"


def test_bare_identifiers(parser):
    """Test autoscoping for bare identifiers."""
    # Test simple bare identifier
    result = parser.parse("x", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "local.x"

    # Test nested bare identifier
    result = parser.parse("user.profile.name", type_check=False)
    assert not result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "local.user.profile.name"


def test_redundant_local_prefix(parser):
    """Test that redundant local. prefix is handled correctly."""
    # Test redundant local prefix
    result = parser.parse("local.x = 42", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.x"

    # Test redundant local prefix in nested path
    result = parser.parse("local.user.profile.name = 'John'", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.user.profile.name"


def test_fstring_autoscoping(parser):
    """Test autoscoping in f-strings."""
    # Test simple f-string with implicit scope
    result = parser.parse('message = f"Hello, {name}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 2
    assert fstring.parts[0] == "Hello, "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "local.name"

    # Test f-string with explicit scope
    result = parser.parse('message = f"Value: {public.value}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 2
    assert fstring.parts[0] == "Value: "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "public.value"

    # Test f-string with nested paths
    result = parser.parse('message = f"User: {user.profile.name}"', type_check=False)
    assert not result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 2
    assert fstring.parts[0] == "User: "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "local.user.profile.name"

    # Test f-string with mixed scopes
    result = parser.parse('message = f"Config: {system.config.value}, User: {user.name}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 4
    assert fstring.parts[0] == "Config: "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "system.config.value"
    assert fstring.parts[2] == ", User: "
    assert isinstance(fstring.parts[3], Identifier)
    assert fstring.parts[3].name == "local.user.name"


def test_autoscoping_basics(parser, context):
    """Test basic automatic scoping functionality."""
    # Create an interpreter
    interpreter = create_interpreter(context)

    # Parse a program with unscoped variables
    result = parser.parse("private.x = 42\nprivate.y = private.x + 10")
    assert isinstance(result, ParseResult)
    assert result.is_valid

    # Execute the program
    interpreter.execute_program(result)

    # Check that variables were scoped correctly
    assert context.get("private.x") == 42
    assert context.get("private.y") == 52


def test_autoscoping_with_explicit_scopes(parser, context):
    """Test automatic scoping with explicit scopes."""
    # Create an interpreter
    interpreter = create_interpreter(context)

    # Parse a program with mixed scoping
    result = parser.parse("private.x = 42\npublic.y = private.x + 10")
    assert isinstance(result, ParseResult)
    assert result.is_valid

    # Execute the program
    interpreter.execute_program(result)

    # Check that variables were scoped correctly
    assert context.get("private.x") == 42
    assert context.get("public.y") == 52
