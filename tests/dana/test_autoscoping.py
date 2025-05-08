"""Tests for DANA's autoscoping behavior."""

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    FStringExpression,
    Identifier,
)
from opendxa.dana.language.parser import parse


def test_implicit_private_scope():
    """Test that variables without scope prefix are treated as private."""
    # Test simple assignment
    result = parse("x = 42", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.x"

    # Test nested assignment
    result = parse("user.profile.name = 'John'", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.user.profile.name"


def test_explicit_scope_preservation():
    """Test that explicit scope prefixes are preserved."""
    # Test public scope
    result = parse("public.x = 42", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "public.x"

    # Test system scope
    result = parse("system.config.value = true", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "system.config.value"


def test_binary_expressions():
    """Test autoscoping in binary expressions."""
    # Test simple binary expression
    result = parse("y = x + 10", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.y"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "private.x"

    # Test complex binary expression
    result = parse("result = a + b * c", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.result"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "private.a"
    assert stmt.value.right.left.name == "private.b"
    assert stmt.value.right.right.name == "private.c"


def test_mixed_scope_expressions():
    """Test expressions mixing implicit and explicit scopes."""
    # Test mixed scope binary expression
    result = parse("y = x + public.value", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.y"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "private.x"
    assert stmt.value.right.name == "public.value"

    # Test nested mixed scope
    result = parse("result = user.profile.name + system.config.value", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.result"
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.left.name == "private.user.profile.name"
    assert stmt.value.right.name == "system.config.value"


def test_bare_identifiers():
    """Test autoscoping for bare identifiers."""
    # Test simple bare identifier
    result = parse("x", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "private.x"

    # Test nested bare identifier
    result = parse("user.profile.name", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "private.user.profile.name"


def test_redundant_private_prefix():
    """Test that redundant private. prefix is handled correctly."""
    # Test redundant private prefix
    result = parse("private.x = 42", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.x"

    # Test redundant private prefix in nested path
    result = parse("private.user.profile.name = 'John'", type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.user.profile.name"


def test_fstring_autoscoping():
    """Test autoscoping in f-strings."""
    # Test simple f-string with implicit scope
    result = parse('message = f"Hello, {name}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 2
    assert fstring.parts[0] == "Hello, "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "private.name"

    # Test f-string with explicit scope
    result = parse('message = f"Value: {public.value}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 2
    assert fstring.parts[0] == "Value: "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "public.value"

    # Test f-string with nested paths
    result = parse('message = f"User: {user.profile.name}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 2
    assert fstring.parts[0] == "User: "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "private.user.profile.name"

    # Test f-string with mixed scopes
    result = parse('message = f"Config: {system.config.value}, User: {user.name}"', type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.message"
    fstring = stmt.value.literal.value
    assert isinstance(fstring, FStringExpression)
    assert len(fstring.parts) == 4
    assert fstring.parts[0] == "Config: "
    assert isinstance(fstring.parts[1], Identifier)
    assert fstring.parts[1].name == "system.config.value"
    assert fstring.parts[2] == ", User: "
    assert isinstance(fstring.parts[3], Identifier)
    assert fstring.parts[3].name == "private.user.name"
