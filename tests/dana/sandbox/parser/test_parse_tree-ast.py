#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
from typing import cast

import pytest

from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    AttributeAccess,
    BinaryExpression,
    BinaryOperator,
    FStringExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    UnaryExpression,
)
from opendxa.dana.sandbox.parser.transformer.expression_transformer import ExpressionTransformer
from opendxa.dana.sandbox.parser.transformer.fstring_transformer import FStringTransformer
from opendxa.dana.sandbox.parser.transformer.statement_transformer import StatementTransformer
from opendxa.dana.sandbox.parser.transformer.variable_transformer import VariableTransformer

# 1. VariableTransformer tests


def make_token(type_, value):
    class FakeToken:
        def __init__(self, value):
            self.type = type_
            self.value = value

        def __str__(self):
            return str(self.value)

        def __repr__(self):
            return str(self.value)

    return FakeToken(value)


def test_simple_name():
    vt = VariableTransformer()
    token = make_token("NAME", "foo")
    result = vt.simple_name([token])
    assert isinstance(result, Identifier)
    assert result.name == "local.foo"


def test_dotted_access():
    vt = VariableTransformer()
    token1 = make_token("NAME", "foo")
    token2 = make_token("NAME", "bar")
    result = vt.dotted_access([token1, token2])
    assert isinstance(result, Identifier)
    assert result.name == "local.foo.bar"


def test_scoped_var():
    vt = VariableTransformer()
    scope = make_token("SCOPE", "private")
    var = make_token("NAME", "x")
    result = vt.scoped_var([scope, var])
    assert isinstance(result, Identifier)
    assert result.name == "private.x"


def test_identifier_utility():
    vt = VariableTransformer()
    token1 = make_token("NAME", "foo")
    token2 = make_token("NAME", "bar")
    result = vt.identifier([token1, token2])
    assert isinstance(result, Identifier)
    assert result.name == "local.foo.bar"


def test_variable_scoped_and_dotted():
    vt = VariableTransformer()
    token_scope = make_token("SCOPE", "private")
    token_name = make_token("NAME", "foo")
    result_scoped = vt.scoped_var([token_scope, token_name])
    result_dotted = vt.dotted_access([token_name, token_name])
    assert result_scoped.name == "private.foo"
    assert result_dotted.name == "local.foo.foo"


# 2. FStringTransformer tests


def test_fstring_text_only():
    ft = FStringTransformer()
    token = make_token("REGULAR_STRING", "Hello world!")
    result = ft.f_string([token])
    assert isinstance(result, LiteralExpression)
    fexpr = result.value
    assert isinstance(fexpr, FStringExpression)
    assert fexpr.parts == ["Hello world!"]


def test_fstring_with_identifier():
    ft = FStringTransformer()
    token = make_token("REGULAR_STRING", "Hello, {foo}")
    result = ft.f_string([token])
    fexpr = result.value
    assert isinstance(fexpr, FStringExpression)
    assert fexpr.parts[0] == "Hello, "
    assert isinstance(fexpr.parts[1], Identifier)
    assert fexpr.parts[1].name == "local.foo"


def test_fstring_with_binary_expression():
    ft = FStringTransformer()
    token = make_token("REGULAR_STRING", "Sum: {x + y}")
    result = ft.f_string([token])
    fexpr = result.value
    assert isinstance(fexpr, FStringExpression)
    assert fexpr.parts[0] == "Sum: "
    bexpr = fexpr.parts[1]
    assert isinstance(bexpr, BinaryExpression)
    assert bexpr.operator == BinaryOperator.ADD
    assert isinstance(bexpr.left, Identifier)
    assert bexpr.left.name == "local.x"
    assert isinstance(bexpr.right, Identifier)
    assert bexpr.right.name == "local.y"


def test_fstring_unbalanced_braces():
    ft = FStringTransformer()
    token = make_token("REGULAR_STRING", "Hello {foo")
    with pytest.raises(ValueError):
        ft.f_string([token])


def test_fstring_multiple_and_expression():
    ft = FStringTransformer()
    token = make_token("REGULAR_STRING", "A: {a}, B: {b + 1}")
    result = ft.f_string([token])
    fexpr = result.value
    assert isinstance(fexpr, FStringExpression)
    assert len(fexpr.parts) == 4
    assert isinstance(fexpr.parts[1], Identifier)
    assert isinstance(fexpr.parts[3], BinaryExpression)


# 3. StatementTransformer tests


def test_statement_assignment():
    st = StatementTransformer()
    target = Identifier(name="local.x")
    value = LiteralExpression(value=1)
    stmt = st.assignment([target, value])
    assert stmt.target.name == "local.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.value == 1


def test_statement_conditional():
    st = StatementTransformer()
    cond = BinaryExpression(left=Identifier("local.x"), operator=BinaryOperator.GREATER_THAN, right=LiteralExpression(0))
    if_body = [Assignment(target=Identifier("local.x"), value=LiteralExpression(1))]
    else_body = [Assignment(target=Identifier("local.x"), value=LiteralExpression(2))]
    conditional = st.conditional([[cond] + if_body, else_body])
    assert conditional.condition.operator == BinaryOperator.GREATER_THAN
    assert len(conditional.body) == 1
    assert len(conditional.else_body) == 1


def test_statement_while_loop():
    st = StatementTransformer()
    cond = BinaryExpression(left=Identifier("local.x"), operator=BinaryOperator.LESS_THAN, right=LiteralExpression(10))
    body = [
        Assignment(
            target=Identifier("local.x"),
            value=BinaryExpression(left=Identifier("local.x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
        )
    ]
    loop = st.while_stmt([cond] + body)
    assert loop.condition.operator == BinaryOperator.LESS_THAN
    assert len(loop.body) == 1


def test_statement_for_loop():
    st = StatementTransformer()
    _ = Identifier("local.i")
    iterable = Identifier("local.xs")
    body = [Assignment(target=Identifier("local.i"), value=LiteralExpression(1))]
    loop = st.for_stmt([make_token("NAME", "i"), iterable, body])
    assert loop.target.name == "i"
    assert loop.iterable.name == "local.xs"
    assert len(loop.body) == 1


def test_statement_function_def():
    st = StatementTransformer()
    name = make_token("NAME", "foo")
    parameters = [Identifier("local.x")]
    body = [Assignment(target=Identifier("local.x"), value=LiteralExpression(1))]
    func = st.function_def([name, parameters, body])
    assert func.name.name == "foo"
    assert func.parameters[0].name == "local.x"
    assert len(func.body) == 1


def test_statement_return_break_continue_pass():
    st = StatementTransformer()
    ret = st.return_stmt([LiteralExpression(1)]).value
    assert isinstance(ret, LiteralExpression)
    assert ret.value == 1
    assert st.break_stmt([]) is not None
    assert st.continue_stmt([]) is not None
    assert st.pass_stmt([]) is not None


# 4. ExpressionTransformer tests


def test_expression_arithmetic():
    et = ExpressionTransformer()
    a = LiteralExpression(2)
    b = LiteralExpression(3)
    expr_add = et.sum_expr([a, "+", b])
    expr_mul = et.term([a, "*", b])
    assert isinstance(expr_add, BinaryExpression)
    expr_add = cast(BinaryExpression, expr_add)
    assert expr_add.operator == BinaryOperator.ADD
    assert isinstance(expr_mul, BinaryExpression)
    expr_mul = cast(BinaryExpression, expr_mul)
    assert expr_mul.operator == BinaryOperator.MULTIPLY


def test_expression_logical():
    et = ExpressionTransformer()
    a = Identifier("local.a")
    b = Identifier("local.b")
    c = Identifier("local.c")
    expr = et.or_expr([et.and_expr([a, b]), c])
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.OR
    assert isinstance(expr.left, BinaryExpression)
    assert expr.left.operator == BinaryOperator.AND


def test_expression_comparison():
    et = ExpressionTransformer()
    x = Identifier("local.x")
    zero = LiteralExpression(0)
    expr = et.comparison([x, ">", zero])
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.GREATER_THAN
    assert expr.left.name == "local.x"
    assert expr.right.value == 0


def test_expression_unary_not():
    et = ExpressionTransformer()
    x = Identifier("local.x")
    expr = et.not_expr(["not", x])
    assert isinstance(expr, UnaryExpression)
    assert expr.operator == "not"
    assert expr.operand.name == "local.x"


def test_expression_arithmetic_ops():
    et = ExpressionTransformer()
    a = LiteralExpression(2)
    b = LiteralExpression(3)
    expr_add = et.sum_expr([a, "+", b])
    expr_mul = et.term([a, "*", b])
    expr_add = cast(BinaryExpression, expr_add)
    assert expr_add.operator == BinaryOperator.ADD
    expr_mul = cast(BinaryExpression, expr_mul)
    assert expr_mul.operator == BinaryOperator.MULTIPLY


def test_expression_comparison_and_logical():
    et = ExpressionTransformer()
    a = Identifier("local.a")
    b = Identifier("local.b")
    expr_eq = et.comparison([a, "==", b])
    expr_and = et.and_expr([a, "and", b])
    expr_not = et.not_expr(["not", a])
    assert isinstance(expr_eq, BinaryExpression)
    expr_eq = cast(BinaryExpression, expr_eq)
    assert expr_eq.operator == BinaryOperator.EQUALS
    assert isinstance(expr_and, BinaryExpression)
    expr_and = cast(BinaryExpression, expr_and)
    assert expr_and.operator == BinaryOperator.AND
    assert isinstance(expr_not, UnaryExpression)
    assert expr_not.operator == "not"


def test_expression_function_call_and_attr():
    call = FunctionCall(name="local.foo", args={"__positional": [LiteralExpression(1), LiteralExpression(2)]})
    assert call.name == "local.foo"
    assert call.args["__positional"][0].value == 1
    attr = AttributeAccess(object=Identifier("local.foo"), attribute="bar")
    assert attr.object.name == "local.foo"
    assert attr.attribute == "bar"


def test_expression_literals_and_collections():
    et = ExpressionTransformer()
    assert cast(LiteralExpression, et.literal([LiteralExpression(True)])).value is True
    assert cast(LiteralExpression, et.literal([LiteralExpression(None)])).value is None
    assert isinstance(cast(LiteralExpression, et.list([LiteralExpression(1), LiteralExpression(2)])).value, list)
