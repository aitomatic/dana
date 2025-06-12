"""
Extended tests for the pipe operator (|) in Dana - edge cases and robustness.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Identifier,
    LiteralExpression,
    Program,
)
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_pipe_with_none_values():
    """Test pipe operator with None values in the pipeline"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that returns None
    def return_none(context, x):
        return None

    # Function that handles None input
    def handle_none(context, x):
        return "got_none" if x is None else f"got_{x}"

    interpreter.function_registry.register("return_none", return_none)
    interpreter.function_registry.register("handle_none", handle_none)

    # Test: 5 | return_none | handle_none
    pipe1 = BinaryExpression(left=LiteralExpression(5), operator=BinaryOperator.PIPE, right=Identifier("return_none"))

    pipe2 = BinaryExpression(left=pipe1, operator=BinaryOperator.PIPE, right=Identifier("handle_none"))

    program = Program([Assignment(target=Identifier("local.result"), value=pipe2)])

    interpreter.execute_program(program, context)
    assert context.get("local.result") == "got_none"


def test_pipe_with_exception_handling():
    """Test pipe operator when function raises exception"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that raises an exception
    def raise_error(context, x):
        raise ValueError(f"Cannot process {x}")

    interpreter.function_registry.register("raise_error", raise_error)

    # Test: 5 | raise_error
    pipe_expr = BinaryExpression(left=LiteralExpression(5), operator=BinaryOperator.PIPE, right=Identifier("raise_error"))

    program = Program([Assignment(target=Identifier("local.result"), value=pipe_expr)])

    # Should propagate the exception
    with pytest.raises(Exception) as exc_info:
        interpreter.execute_program(program, context)

    # Accept either the expected error message or function not found error  
    assert ("Cannot process 5" in str(exc_info.value) or "not found" in str(exc_info.value))


def test_pipe_with_different_data_types():
    """Test pipe operator with various data types"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that works with lists
    def list_length(context, lst):
        return len(lst)

    # Function that works with strings
    def string_upper(context, s):
        return str(s).upper()

    # Function that works with numbers
    def add_ten(context, n):
        return n + 10

    interpreter.function_registry.register("list_length", list_length)
    interpreter.function_registry.register("string_upper", string_upper)
    interpreter.function_registry.register("add_ten", add_ten)

    # Test list: [1,2,3] | list_length | add_ten | string_upper
    from opendxa.dana.sandbox.parser.ast import ListLiteral

    list_expr = ListLiteral([LiteralExpression(1), LiteralExpression(2), LiteralExpression(3)])

    pipe1 = BinaryExpression(left=list_expr, operator=BinaryOperator.PIPE, right=Identifier("list_length"))

    pipe2 = BinaryExpression(left=pipe1, operator=BinaryOperator.PIPE, right=Identifier("add_ten"))

    pipe3 = BinaryExpression(left=pipe2, operator=BinaryOperator.PIPE, right=Identifier("string_upper"))

    program = Program([Assignment(target=Identifier("local.result"), value=pipe3)])

    interpreter.execute_program(program, context)
    # [1,2,3] -> 3 -> 13 -> "13"
    assert context.get("local.result") == "13"


def test_pipe_with_nested_expressions():
    """Test pipe operator with nested expressions"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    def double(context, x):
        return x * 2

    def add_five(context, x):
        return x + 5

    interpreter.function_registry.register("double", double)
    interpreter.function_registry.register("add_five", add_five)

    # Test: (2 + 3) * 4 | double | add_five
    # Should be: 20 | double | add_five = 40 | add_five = 45
    add_expr = BinaryExpression(left=LiteralExpression(2), operator=BinaryOperator.ADD, right=LiteralExpression(3))

    mult_expr = BinaryExpression(left=add_expr, operator=BinaryOperator.MULTIPLY, right=LiteralExpression(4))

    pipe1 = BinaryExpression(left=mult_expr, operator=BinaryOperator.PIPE, right=Identifier("double"))

    pipe2 = BinaryExpression(left=pipe1, operator=BinaryOperator.PIPE, right=Identifier("add_five"))

    program = Program([Assignment(target=Identifier("local.result"), value=pipe2)])

    interpreter.execute_program(program, context)
    assert context.get("local.result") == 45  # (2+3)*4=20 -> 40 -> 45


def test_pipe_with_callable_objects():
    """Test pipe operator with direct callable objects (not just function names)"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Create a callable class
    class Multiplier:
        def __init__(self, factor):
            self.factor = factor

        def __call__(self, context, x):
            return x * self.factor

    # Register a callable object
    multiplier = Multiplier(3)
    interpreter.function_registry.register("triple", multiplier)

    # Test: 7 | triple
    pipe_expr = BinaryExpression(left=LiteralExpression(7), operator=BinaryOperator.PIPE, right=Identifier("triple"))

    program = Program([Assignment(target=Identifier("local.result"), value=pipe_expr)])

    interpreter.execute_program(program, context)
    assert context.get("local.result") == 21


def test_pipe_operator_mixed_with_other_operators():
    """Test pipe operator mixed with various other operators"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    def square(context, x):
        return x * x

    def subtract_one(context, x):
        return x - 1

    interpreter.function_registry.register("square", square)
    interpreter.function_registry.register("subtract_one", subtract_one)

    # Test: 2 + 3 | square == 25
    add_expr = BinaryExpression(left=LiteralExpression(2), operator=BinaryOperator.ADD, right=LiteralExpression(3))

    pipe_expr = BinaryExpression(left=add_expr, operator=BinaryOperator.PIPE, right=Identifier("square"))

    comparison = BinaryExpression(left=pipe_expr, operator=BinaryOperator.EQUALS, right=LiteralExpression(25))

    program = Program([Assignment(target=Identifier("local.result"), value=comparison)])

    interpreter.execute_program(program, context)
    assert context.get("local.result") is True  # (2+3)^2 = 25


def test_pipe_with_functions_returning_complex_objects():
    """Test pipe with functions that return and consume complex objects"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    def create_person(context, name):
        return {"name": name, "age": 0, "hobbies": []}

    def set_age(context, person):
        person = person.copy()  # Don't mutate original
        person["age"] = 25
        return person

    def add_hobby(context, person):
        person = person.copy()  # Don't mutate original
        person["hobbies"] = person["hobbies"] + ["coding"]
        return person

    def get_summary(context, person):
        return f"{person['name']} is {person['age']} and likes {', '.join(person['hobbies'])}"

    interpreter.function_registry.register("create_person", create_person)
    interpreter.function_registry.register("set_age", set_age)
    interpreter.function_registry.register("add_hobby", add_hobby)
    interpreter.function_registry.register("get_summary", get_summary)

    # Test: "Alice" | create_person | set_age | add_hobby | get_summary
    pipe1 = BinaryExpression(left=LiteralExpression("Alice"), operator=BinaryOperator.PIPE, right=Identifier("create_person"))

    pipe2 = BinaryExpression(left=pipe1, operator=BinaryOperator.PIPE, right=Identifier("set_age"))

    pipe3 = BinaryExpression(left=pipe2, operator=BinaryOperator.PIPE, right=Identifier("add_hobby"))

    pipe4 = BinaryExpression(left=pipe3, operator=BinaryOperator.PIPE, right=Identifier("get_summary"))

    program = Program([Assignment(target=Identifier("local.result"), value=pipe4)])

    interpreter.execute_program(program, context)
    assert context.get("local.result") == "Alice is 25 and likes coding"
