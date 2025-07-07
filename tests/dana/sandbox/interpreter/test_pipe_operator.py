"""
Tests for the pipe operator (|) in Dana.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Identifier,
    LiteralExpression,
    Program,
)
from dana.core.lang.sandbox_context import SandboxContext


def test_basic_pipe_operation():
    """Test basic pipe operation: 5 | double | stringify"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register test functions
    def double(context, x):
        return x * 2

    def stringify(context, x):
        return str(x)

    interpreter.function_registry.register("double", double)
    interpreter.function_registry.register("stringify", stringify)

    # Create pipe expression: 5 | double | stringify
    # This should be evaluated as: stringify(context, double(context, 5))
    double_expr = BinaryExpression(left=LiteralExpression(5), operator=BinaryOperator.PIPE, right=Identifier("double"))

    pipe_expr = BinaryExpression(left=double_expr, operator=BinaryOperator.PIPE, right=Identifier("stringify"))

    program = Program([Assignment(target=Identifier("local:result"), value=pipe_expr)])

    interpreter.execute_program(program, context)
    assert context.get("local:result") == "10"


def test_pipe_with_context_detection():
    """Test that pipe operator correctly detects context requirements"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that expects context as first parameter
    def func_with_context(context, x):
        return x * 3

    # Function that doesn't expect context
    def func_without_context(x):
        return x + 10

    interpreter.function_registry.register("with_context", func_with_context)
    interpreter.function_registry.register("without_context", func_without_context)

    # Create pipe expressions
    pipe_expr1 = BinaryExpression(left=LiteralExpression(5), operator=BinaryOperator.PIPE, right=Identifier("with_context"))

    pipe_expr2 = BinaryExpression(left=LiteralExpression(5), operator=BinaryOperator.PIPE, right=Identifier("without_context"))

    program = Program(
        [Assignment(target=Identifier("local:result1"), value=pipe_expr1), Assignment(target=Identifier("local:result2"), value=pipe_expr2)]
    )

    interpreter.execute_program(program, context)
    assert context.get("local:result1") == 15  # 5 * 3
    assert context.get("local:result2") == 15  # 5 + 10


def test_pipe_with_multiple_args_function():
    """Test pipe with function that returns multiple values"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that takes an ID and returns user data
    def get_user(context, user_id):
        return {"id": user_id, "name": f"User{user_id}", "active": True}

    # Function that enriches user data
    def enrich_user(context, user_data):
        user_data["enriched"] = True
        user_data["timestamp"] = "2025-01-31"
        return user_data

    # Function that converts to JSON string
    def to_json(context, data):
        import json

        return json.dumps(data)

    interpreter.function_registry.register("get_user", get_user)
    interpreter.function_registry.register("enrich_user", enrich_user)
    interpreter.function_registry.register("to_json", to_json)

    # Create pipe expression: 123 | get_user | enrich_user | to_json
    pipe1 = BinaryExpression(left=LiteralExpression(123), operator=BinaryOperator.PIPE, right=Identifier("get_user"))

    pipe2 = BinaryExpression(left=pipe1, operator=BinaryOperator.PIPE, right=Identifier("enrich_user"))

    pipe3 = BinaryExpression(left=pipe2, operator=BinaryOperator.PIPE, right=Identifier("to_json"))

    program = Program([Assignment(target=Identifier("local:result"), value=pipe3)])

    interpreter.execute_program(program, context)
    result = context.get("local:result")

    # Parse the JSON to verify structure
    import json

    data = json.loads(result)
    assert data["id"] == 123
    assert data["name"] == "User123"
    assert data["enriched"] is True
    assert data["timestamp"] == "2025-01-31"


def test_pipe_with_non_callable():
    """Test error handling when right-hand side is not callable"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Set a non-callable value
    context.set("local:not_a_function", 42)

    # Create pipe expression: 5 | not_a_function
    pipe_expr = BinaryExpression(left=LiteralExpression(5), operator=BinaryOperator.PIPE, right=Identifier("not_a_function"))

    program = Program([Assignment(target=Identifier("local:result"), value=pipe_expr)])

    # This should raise an error
    with pytest.raises(Exception) as exc_info:
        interpreter.execute_program(program, context)

    assert "Function 'not_a_function' not found in registry" in str(exc_info.value)


def test_pipe_operator_precedence():
    """Test that pipe operator has correct precedence (lower than method calls)"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register test functions
    def add_one(context, x):
        return x + 1

    def multiply_two(context, x):
        return x * 2

    interpreter.function_registry.register("add_one", add_one)
    interpreter.function_registry.register("multiply_two", multiply_two)

    # Create expression: 3 + 2 | add_one
    # This should be evaluated as: (3 + 2) | add_one = 5 | add_one = 6
    # NOT as: 3 + (2 | add_one)
    add_expr = BinaryExpression(left=LiteralExpression(3), operator=BinaryOperator.ADD, right=LiteralExpression(2))

    pipe_expr = BinaryExpression(left=add_expr, operator=BinaryOperator.PIPE, right=Identifier("add_one"))

    program = Program([Assignment(target=Identifier("local:result"), value=pipe_expr)])

    interpreter.execute_program(program, context)
    assert context.get("local:result") == 6  # (3 + 2) | add_one = 5 | add_one = 6


def test_pipe_left_associativity():
    """Test that pipe operator is left-associative"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register test functions
    def add_ten(context, x):
        return x + 10

    def double(context, x):
        return x * 2

    def subtract_five(context, x):
        return x - 5

    interpreter.function_registry.register("add_ten", add_ten)
    interpreter.function_registry.register("double", double)
    interpreter.function_registry.register("subtract_five", subtract_five)

    # Create expression: 1 | add_ten | double | subtract_five
    # Left-associative means: ((1 | add_ten) | double) | subtract_five
    # = (11 | double) | subtract_five = 22 | subtract_five = 17
    pipe1 = BinaryExpression(left=LiteralExpression(1), operator=BinaryOperator.PIPE, right=Identifier("add_ten"))

    pipe2 = BinaryExpression(left=pipe1, operator=BinaryOperator.PIPE, right=Identifier("double"))

    pipe3 = BinaryExpression(left=pipe2, operator=BinaryOperator.PIPE, right=Identifier("subtract_five"))

    program = Program([Assignment(target=Identifier("local:result"), value=pipe3)])

    interpreter.execute_program(program, context)
    assert context.get("local:result") == 17  # ((1+10)*2)-5 = 17
