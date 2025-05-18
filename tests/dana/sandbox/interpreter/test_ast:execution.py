#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
"""
AST → Execution tests for the DANA interpreter.
Organized by feature for maintainability.
"""
import pytest

from opendxa.dana.sandbox.interpreter.functions.python_function import PythonRegistry
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    Identifier,
    LiteralExpression,
    Program,
    WhileLoop,
)
from opendxa.dana.sandbox.sandbox_context import SandboxContext


# --- Literals ---
def test_integer_literal():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression(42)),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 42


# --- Assignments ---
def test_simple_assignment():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression("foo")),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == "foo"


# --- Arithmetic ---
def test_addition():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.ADD,
                    right=LiteralExpression(3),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 5


# --- Comparison ---
def test_comparison():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.LESS_THAN,
                    right=LiteralExpression(3),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


# --- Control Flow ---
def test_if_statement():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Conditional(
                condition=BinaryExpression(
                    left=LiteralExpression(1),
                    operator=BinaryOperator.EQUALS,
                    right=LiteralExpression(1),
                ),
                body=[Assignment(target=Identifier("private.result"), value=LiteralExpression("yes"))],
                else_body=[Assignment(target=Identifier("private.result"), value=LiteralExpression("no"))],
                line_num=1,
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == "yes"


def test_while_loop():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression(0)),
            WhileLoop(
                condition=BinaryExpression(
                    left=Identifier("private.result"),
                    operator=BinaryOperator.LESS_THAN,
                    right=LiteralExpression(3),
                ),
                body=[
                    Assignment(
                        target=Identifier("private.result"),
                        value=BinaryExpression(
                            left=Identifier("private.result"),
                            operator=BinaryOperator.ADD,
                            right=LiteralExpression(1),
                        ),
                    )
                ],
                line_num=2,
            ),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 3


# --- More Literals ---
def test_float_literal():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression(3.14)),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 3.14


def test_bool_literal():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression(True)),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


def test_none_literal():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression(None)),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is None


def test_list_literal():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=LiteralExpression([1, 2, 3])),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == [1, 2, 3]


def test_fstring_literal():
    from opendxa.dana.sandbox.parser.ast import FStringExpression

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"), value=LiteralExpression(FStringExpression(parts=["foo", LiteralExpression(42)]))
            ),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == "foo42"


# --- More Arithmetic ---
def test_subtraction():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(5),
                    operator=BinaryOperator.SUBTRACT,
                    right=LiteralExpression(2),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 3


def test_multiplication():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.MULTIPLY,
                    right=LiteralExpression(3),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 6


def test_division():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(6),
                    operator=BinaryOperator.DIVIDE,
                    right=LiteralExpression(2),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 3


def test_modulo():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(7),
                    operator=BinaryOperator.MODULO,
                    right=LiteralExpression(4),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 3


def test_power():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.POWER,
                    right=LiteralExpression(3),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 8


# --- More Comparison Operators ---
def test_equals():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.EQUALS,
                    right=LiteralExpression(2),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


def test_not_equals():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.NOT_EQUALS,
                    right=LiteralExpression(3),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


def test_greater_than():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(3),
                    operator=BinaryOperator.GREATER_THAN,
                    right=LiteralExpression(2),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


def test_less_equals():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(2),
                    operator=BinaryOperator.LESS_EQUALS,
                    right=LiteralExpression(2),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


def test_greater_equals():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(3),
                    operator=BinaryOperator.GREATER_EQUALS,
                    right=LiteralExpression(2),
                ),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") is True


# --- Unary Expressions ---
def test_unary_expression():
    from opendxa.dana.sandbox.parser.ast import UnaryExpression

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=UnaryExpression(operator="-", operand=LiteralExpression(5)),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == -5


# --- Function Call ---
@pytest.mark.xfail(reason="FunctionCall not yet implemented")
def test_function_call():
    from opendxa.dana.sandbox.parser.ast import FunctionCall

    interpreter = Interpreter(SandboxContext())
    # Register a dummy function 'foo' that returns 42 and accepts context/kwargs
    PythonRegistry().register("foo", lambda context=None, **kwargs: 42)
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=FunctionCall(name="foo", args={}),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 42


# --- Attribute Access ---
def test_attribute_access():
    from opendxa.dana.sandbox.parser.ast import AttributeAccess, DictLiteral

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=AttributeAccess(object=DictLiteral(items=[(LiteralExpression("x"), LiteralExpression(1))]), attribute="x"),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 1


# --- Subscript Expression ---
def test_subscript_expression():
    from opendxa.dana.sandbox.parser.ast import SubscriptExpression

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=SubscriptExpression(object=LiteralExpression([10, 20]), index=LiteralExpression(1)),
            )
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 20


# --- Tuple/Dict/Set Literals ---
def test_tuple_literal():
    from opendxa.dana.sandbox.parser.ast import TupleLiteral

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=TupleLiteral(items=[LiteralExpression(1), LiteralExpression(2)])),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == (1, 2)


def test_dict_literal():
    from opendxa.dana.sandbox.parser.ast import DictLiteral

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=DictLiteral(items=[(LiteralExpression("a"), LiteralExpression(1))])),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == {"a": 1}


def test_set_literal():
    from opendxa.dana.sandbox.parser.ast import SetLiteral

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(target=Identifier("private.result"), value=SetLiteral(items=[LiteralExpression(1), LiteralExpression(2)])),
        ]
    )
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == {1, 2}


# --- Other Statements ---
def test_print_statement():
    from opendxa.dana.sandbox.parser.ast import PrintStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            PrintStatement(message=LiteralExpression("hello")),
        ]
    )
    interpreter.execute_program(program)
    # No assertion needed, just ensure no error


def test_break_statement():
    from opendxa.dana.sandbox.interpreter.executor.statement_executor import BreakException
    from opendxa.dana.sandbox.parser.ast import BreakStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            BreakStatement(),
        ]
    )
    try:
        interpreter.execute_program(program, suppress_exceptions=False)
    except BreakException:
        pass
    else:
        raise AssertionError("BreakException was not raised")


def test_continue_statement():
    from opendxa.dana.sandbox.interpreter.executor.statement_executor import ContinueException
    from opendxa.dana.sandbox.parser.ast import ContinueStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            ContinueStatement(),
        ]
    )
    try:
        interpreter.execute_program(program, suppress_exceptions=False)
    except ContinueException:
        pass
    else:
        raise AssertionError("ContinueException was not raised")


def test_pass_statement():
    from opendxa.dana.sandbox.parser.ast import PassStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            PassStatement(),
        ]
    )
    interpreter.execute_program(program)


def test_return_statement():
    from opendxa.dana.sandbox.interpreter.executor.statement_executor import ReturnException
    from opendxa.dana.sandbox.parser.ast import ReturnStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            ReturnStatement(value=LiteralExpression(42)),
        ]
    )
    try:
        interpreter.execute_program(program, suppress_exceptions=False)
    except ReturnException as e:
        assert e.value == 42
    else:
        raise AssertionError("ReturnException was not raised")


def test_raise_statement():
    from opendxa.dana.sandbox.parser.ast import RaiseStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            RaiseStatement(value=LiteralExpression("error")),
        ]
    )
    try:
        interpreter.execute_program(program, suppress_exceptions=False)
    except Exception as e:
        assert str(e) == "error"
    else:
        raise AssertionError("Exception was not raised")


def test_assert_statement():
    from opendxa.dana.sandbox.parser.ast import AssertStatement

    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            AssertStatement(condition=LiteralExpression(False), message=LiteralExpression("fail!")),
        ]
    )
    try:
        interpreter.execute_program(program, suppress_exceptions=False)
    except AssertionError as e:
        assert str(e) == "fail!"
    else:
        raise AssertionError("AssertionError was not raised")


# --- Bare Expression as Statement ---
def test_bare_expression_statement():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            LiteralExpression(123),
        ]
    )
    interpreter.execute_program(program)


# --- Negative/Error Case ---
@pytest.mark.xfail(reason="Division by zero error handling not yet implemented")
def test_division_by_zero():
    interpreter = Interpreter(SandboxContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.result"),
                value=BinaryExpression(
                    left=LiteralExpression(1),
                    operator=BinaryOperator.DIVIDE,
                    right=LiteralExpression(0),
                ),
            )
        ]
    )
    interpreter.execute_program(program)


# --- End-to-End Integration Tests for DANA Grammar Features ---
# (Moved to test_code:execution.py)
