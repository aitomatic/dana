#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
"""Unit tests for the DANA language parser."""

import textwrap

import pytest
from lark import Tree

from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    AttributeAccess,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    DictLiteral,
    FStringExpression,
    FunctionCall,
    # Add more as needed for coverage
    Identifier,
    LiteralExpression,
    Program,
    SetLiteral,
    SubscriptExpression,
    TupleLiteral,
    UnaryExpression,
    WhileLoop,
)
from opendxa.dana.sandbox.parser.dana_parser import DanaParser


# === Helper Functions ===
def get_first_statement(program):
    stmt = program.statements[0]
    # Recursively unwrap Tree or list wrappers
    while isinstance(stmt, (Tree, list)):
        if isinstance(stmt, list):
            stmt = stmt[0]
        elif isinstance(stmt, Tree) and stmt.children:
            stmt = stmt.children[0]
        else:
            break
    return stmt


def get_assignment(program):
    stmt = get_first_statement(program)
    # Recursively unwrap Tree or list wrappers
    while not isinstance(stmt, Assignment):
        if isinstance(stmt, list):
            stmt = stmt[0]
        elif isinstance(stmt, Tree) and stmt.children:
            stmt = stmt.children[0]
        else:
            raise AssertionError(f"Could not find Assignment in node: {stmt}")
    return stmt


def get_conditional(program):
    for stmt in program.statements:
        # Recursively unwrap Tree or list wrappers
        s = stmt
        while isinstance(s, (list, Tree)):
            if isinstance(s, list):
                s = s[0]
            elif isinstance(s, Tree) and s.children:
                s = s.children[0]
            else:
                break
        if isinstance(s, Conditional):
            return s
    raise AssertionError("No Conditional found in program.statements")


def get_while_loop(program):
    for stmt in program.statements:
        # Recursively unwrap Tree or list wrappers
        s = stmt
        while isinstance(s, (list, Tree)):
            if isinstance(s, list):
                s = s[0]
            elif isinstance(s, Tree) and s.children:
                s = s.children[0]
            else:
                break
        if isinstance(s, WhileLoop):
            return s
    raise AssertionError("No WhileLoop found in program.statements")


def assert_assignment(node, target_name, value_type=None):
    assert isinstance(node, Assignment)
    assert node.target.name == target_name
    valid_types = (
        LiteralExpression,
        Identifier,
        BinaryExpression,
        # Add all other valid expression node classes as needed
        # These should match the Expression type alias in ast.py
        # If you want to be exhaustive:
        # FunctionCall, FStringExpression, UnaryExpression, AttributeAccess, SubscriptExpression, DictLiteral, SetLiteral, TupleLiteral
        FunctionCall,
        FStringExpression,
        UnaryExpression,
        AttributeAccess,
        SubscriptExpression,
        DictLiteral,
        SetLiteral,
        TupleLiteral,
    )
    if value_type is not None:
        assert isinstance(node.value, value_type)
    else:
        assert isinstance(node.value, valid_types)


# === Pytest Fixture ===
@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return DanaParser()


# Add a fixture for the typecheck flag
@pytest.fixture(params=[True, False], ids=["typecheck_on", "typecheck_off"])
def typecheck_flag(request):
    return request.param


# =========================
# 1. ASSIGNMENTS
# =========================
def test_assignment_simple(parser, typecheck_flag):
    program = parser.parse("x = 42", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.x")
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.value == 42


def test_assignment_float(parser, typecheck_flag):
    program = parser.parse("x = 3.14", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.x")
    assert stmt.value.value == 3.14


def test_assignment_scoped(parser, typecheck_flag):
    program = parser.parse("private:x = 1", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "private.x")
    assert stmt.value.value == 1


def test_assignment_dotted(parser, typecheck_flag):
    program = parser.parse("foo.bar = 2", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.foo.bar")
    assert stmt.value.value == 2


# TODO: Add indexed assignment when supported by AST


# =========================
# 2. LITERALS & STRINGS
# =========================
def test_literal_string(parser, typecheck_flag):
    program = parser.parse('msg = "Alice"', do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.msg")
    assert stmt.value.value == "Alice"


def test_literal_multiline_string(parser, typecheck_flag):
    program = parser.parse('msg = """Hello\nWorld"""', do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.msg")
    assert isinstance(stmt.value, LiteralExpression)
    assert isinstance(stmt.value.value, str)
    assert "Hello" in stmt.value.value


def test_literal_fstring(parser, typecheck_flag):
    program = parser.parse('msg = f"Hello, {name}"', do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.msg")
    assert isinstance(stmt.value, LiteralExpression)
    assert isinstance(stmt.value.value, FStringExpression)


def test_literal_raw_string(parser, typecheck_flag):
    program = parser.parse('msg = r"raw\\nstring"', do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.msg")
    assert isinstance(stmt.value, LiteralExpression)
    assert isinstance(stmt.value.value, str)
    assert "raw" in stmt.value.value


def test_literal_bool_and_none(parser, typecheck_flag):
    program = parser.parse("a = True\nb = False\nc = None", do_type_check=typecheck_flag, do_transform=True)
    assert len(program.statements) == 3
    assert all(isinstance(get_assignment(type("FakeProg", (), {"statements": [stmt]})()), Assignment) for stmt in program.statements)
    value = program.statements[0].value
    if hasattr(value, "data") and hasattr(value, "children"):
        # Unwrap Tree to get the actual value
        value = value.children[0] if value.children else value
    assert isinstance(value, LiteralExpression)
    assert value.value is True
    assert isinstance(program.statements[1].value, LiteralExpression)
    assert program.statements[1].value.value is False
    assert isinstance(program.statements[2].value, LiteralExpression)
    assert program.statements[2].value.value is None


# =========================
# 3. COLLECTIONS
# =========================
def test_collection_list(parser, typecheck_flag):
    program = parser.parse("l = [1, 2]", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.l")
    assert isinstance(stmt.value, LiteralExpression)
    assert isinstance(stmt.value.value, list)
    assert all(isinstance(e, LiteralExpression) for e in stmt.value.value)
    assert [e.value for e in stmt.value.value] == [1, 2]


def test_collection_dict(parser, typecheck_flag):
    program = parser.parse('d = {"a": 1, "b": 2}', do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert_assignment(stmt, "local.d")
    assert hasattr(stmt.value, "items")
    assert len(stmt.value.items) == 2
    for (k, v), (ek, ev) in zip(
        stmt.value.items, [(LiteralExpression("a"), LiteralExpression(1)), (LiteralExpression("b"), LiteralExpression(2))]
    ):
        assert isinstance(k, LiteralExpression)
        assert isinstance(v, LiteralExpression)
        assert k.value == ek.value
        assert v.value == ev.value


def test_collection_tuple(parser, typecheck_flag):
    program = parser.parse("t = (1, 2)", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    assert hasattr(stmt.value, "items")
    assert stmt.value.items == [LiteralExpression(value=1), LiteralExpression(value=2)]


def test_collection_empty(parser, typecheck_flag):
    program = parser.parse("a = []\nb = {}\nc = ()", do_type_check=typecheck_flag, do_transform=True)
    assert len(program.statements) == 3


# =========================
# 4. EXPRESSIONS
# =========================
def test_expression_arithmetic(parser, typecheck_flag):
    program = parser.parse("x = 1 + 2 * 3", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    expr = stmt.value
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.ADD
    assert isinstance(expr.right, BinaryExpression)
    assert expr.right.operator == BinaryOperator.MULTIPLY


def test_expression_parentheses(parser, typecheck_flag):
    program = parser.parse("x = (1 + 2) * 3", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    expr = stmt.value
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.MULTIPLY
    assert isinstance(expr.left, BinaryExpression)
    assert expr.left.operator == BinaryOperator.ADD


def test_expression_logical(parser, typecheck_flag):
    program = parser.parse("x = True and False or not True", do_type_check=typecheck_flag, do_transform=True)
    stmt = get_assignment(program)
    expr = stmt.value
    assert isinstance(expr, BinaryExpression)
    # Check for AND/OR/NOT in the tree
    assert any(
        op in [BinaryOperator.AND, BinaryOperator.OR]
        for op in [getattr(expr, "operator", None), getattr(getattr(expr, "left", None), "operator", None)]
    )


# =========================
# 5. CONTROL FLOW
# =========================
def test_if_else(parser, typecheck_flag):
    code = textwrap.dedent(
        """
    x = 0
    if x > 10:
        y = 1
    else:
        y = 2
    """
    )
    program = parser.parse(code, do_type_check=typecheck_flag, do_transform=True)
    stmt = get_conditional(program)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.GREATER_THAN
    assert len(stmt.body) == 1
    assert len(stmt.else_body) == 1


def test_while_loop(parser, typecheck_flag):
    code = textwrap.dedent(
        """
    x = 0
    while x < 10:
        x = x + 1
    """
    )
    program = parser.parse(code, do_type_check=typecheck_flag, do_transform=True)
    stmt = get_while_loop(program)
    assert isinstance(stmt, WhileLoop)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.LESS_THAN
    assert len(stmt.body) == 1


# TODO: Add for-loop, minimal/nested blocks, elif, try/except/finally

# =========================
# 6. FUNCTIONS & CALLS
# =========================
# TODO: Add function definition, function call, nested calls, minimal function

# =========================
# 7. IMPORTS & SCOPE
# =========================
# TODO: Add import statement, from-import, scope edge cases

# =========================
# 8. TRY/EXCEPT/FINALLY
# =========================
# TODO: Add try/except, try/except/finally, raise, assert

# =========================
# 9. PASS/RETURN/BREAK/CONTINUE
# =========================
# TODO: Add pass, return, break, continue

# =========================
# 10. PROPERTY ACCESS & TRAILER
# =========================
# TODO: Add property access, chained calls, indexing


# =========================
# 11. MISCELLANEOUS
# =========================
def test_multiple_statements(parser, typecheck_flag):
    program = parser.parse('x = 42\ny = "test"\nlog("done")', do_type_check=typecheck_flag, do_transform=True)
    assert isinstance(program, Program)
    assert len(program.statements) == 3


def test_bare_identifier(parser, typecheck_flag):
    code = "private:x = 1\nprivate:x"
    program = parser.parse(code, do_type_check=typecheck_flag, do_transform=True)
    # First statement: assignment
    stmt1 = program.statements[0]
    assert hasattr(stmt1, "target") and stmt1.target.name == "private.x"
    # Second statement: bare identifier
    stmt2 = program.statements[1]
    if hasattr(stmt2, "name"):
        assert stmt2.name == "private.x"
    elif hasattr(stmt2, "target"):
        assert stmt2.target.name == "private.x"
    else:
        raise AssertionError(f"Unexpected statement type: {type(stmt2)}")


# =========================
# 12. NEGATIVE/ERROR CASES
# =========================
def test_incomplete_assignment_error(parser, typecheck_flag):
    with pytest.raises(Exception):  # noqa: B017
        parser.parse("x =", do_type_check=typecheck_flag, do_transform=True)


def test_unmatched_parentheses_error(parser, typecheck_flag):
    with pytest.raises(Exception):  # noqa: B017
        parser.parse("x = (1 + 2", do_type_check=typecheck_flag, do_transform=True)


def test_invalid_keyword_error(parser, typecheck_flag):
    import lark

    try:
        parser.parse("foo = break", do_type_check=typecheck_flag, do_transform=True)
    except lark.exceptions.UnexpectedToken:
        return  # Expected
    except Exception:
        return
    raise AssertionError("Expected an exception for invalid keyword, but none was raised.")


def test_type_error_mismatched_types(parser):
    code = "x = 1\nx = x + 'a'"
    with pytest.raises(Exception):  # noqa: B017
        parser.parse(code, do_type_check=True, do_transform=True)


def test_type_error_undefined_variable(parser):
    code = "y = x + 1"
    with pytest.raises(Exception):  # noqa: B017
        parser.parse(code, do_type_check=True, do_transform=True)


def test_type_error_invalid_operation(parser):
    code = "x = 'hello' - 1"
    with pytest.raises(Exception):  # noqa: B017
        parser.parse(code, do_type_check=True, do_transform=True)


def test_syntax_error_malformed_block(parser):
    code = "if x > 0:\n    y = 1\nelse:"
    with pytest.raises(Exception):  # noqa: B017
        parser.parse(code, do_type_check=False, do_transform=True)


# =========================
# 13. EDGE CASES & TODOs
# =========================
# TODO: Cover for-loop, function def/call, import, try/except/finally, pass/return/break/continue, property access, trailers, more error cases, only comments, blank lines, minimal/nested blocks, etc.
# See test_parse.py for more ideas.
