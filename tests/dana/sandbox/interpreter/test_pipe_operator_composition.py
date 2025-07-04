"""
Tests for function composition with the pipe operator (|) in Dana.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    FunctionCall,
    Identifier,
    LiteralExpression,
    Program,
)
from dana.core.lang.sandbox_context import SandboxContext


def test_basic_function_composition():
    """Test basic function composition: f = double | stringify"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register test functions
    def double(context, x):
        return x * 2

    def stringify(context, x):
        return str(x)

    interpreter.function_registry.register("double", double)
    interpreter.function_registry.register("stringify", stringify)

    # Create composed function: f = double | stringify
    composition = BinaryExpression(left=Identifier("double"), operator=BinaryOperator.PIPE, right=Identifier("stringify"))

    program = Program([Assignment(target=Identifier("local:f"), value=composition)])

    interpreter.execute_program(program, context)

    # Get the composed function
    composed_func = context.get("local:f")
    assert hasattr(composed_func, "_is_dana_composed_function")

    # Test the composed function
    result = composed_func(context, 5)
    assert result == "10"  # double(5) = 10, stringify(10) = "10"


def test_composed_function_call():
    """Test calling a composed function through the function call interface"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register test functions
    def add_one(context, x):
        return x + 1

    def multiply_three(context, x):
        return x * 3

    interpreter.function_registry.register("add_one", add_one)
    interpreter.function_registry.register("multiply_three", multiply_three)

    # Create composed function: f = add_one | multiply_three
    composition = BinaryExpression(left=Identifier("add_one"), operator=BinaryOperator.PIPE, right=Identifier("multiply_three"))

    # Register the composed function in the registry
    program = Program([Assignment(target=Identifier("local:f"), value=composition)])

    interpreter.execute_program(program, context)
    composed_func = context.get("local:f")

    # Register the composed function so it can be called by name
    interpreter.function_registry.register("f", composed_func)

    # Create a function call: result = f(7)
    func_call = FunctionCall(name="f", args={"0": LiteralExpression(7)})

    program = Program([Assignment(target=Identifier("local:result"), value=func_call)])

    interpreter.execute_program(program, context)

    # Should be: add_one(7) = 8, multiply_three(8) = 24
    assert context.get("local:result") == 24


def test_chained_function_composition():
    """Test chained function composition: f = f1 | f2 | f3"""
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

    # Create chained composition: f = add_ten | double | subtract_five
    # Left-associative: ((add_ten | double) | subtract_five)
    comp1 = BinaryExpression(left=Identifier("add_ten"), operator=BinaryOperator.PIPE, right=Identifier("double"))

    comp2 = BinaryExpression(left=comp1, operator=BinaryOperator.PIPE, right=Identifier("subtract_five"))

    program = Program([Assignment(target=Identifier("local:f"), value=comp2)])

    interpreter.execute_program(program, context)

    # Get and test the composed function
    composed_func = context.get("local:f")
    result = composed_func(context, 1)

    # Should be: add_ten(1) = 11, double(11) = 22, subtract_five(22) = 17
    assert result == 17


def test_composition_vs_data_pipeline():
    """Test that function composition and data pipeline work correctly together"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register test functions
    def add_five(context, x):
        return x + 5

    def multiply_two(context, x):
        return x * 2

    interpreter.function_registry.register("add_five", add_five)
    interpreter.function_registry.register("multiply_two", multiply_two)

    # Create composed function: f = add_five | multiply_two
    composition = BinaryExpression(left=Identifier("add_five"), operator=BinaryOperator.PIPE, right=Identifier("multiply_two"))

    # Create data pipeline: result = 3 | f
    # Here f is the composed function, 3 is data
    pipe3 = BinaryExpression(left=LiteralExpression(3), operator=BinaryOperator.PIPE, right=composition)

    program = Program([Assignment(target=Identifier("local:result"), value=pipe3)])

    interpreter.execute_program(program, context)

    # Should be: add_five(3) = 8, multiply_two(8) = 16
    assert context.get("local:result") == 16


def test_composed_function_with_different_context_requirements():
    """Test composed functions with mixed context requirements"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that needs context
    def func_with_context(context, x):
        return x * 2

    # Function that doesn't need context
    def func_without_context(x):
        return x + 10

    interpreter.function_registry.register("with_context", func_with_context)
    interpreter.function_registry.register("without_context", func_without_context)

    # Create composition: f = with_context | without_context
    composition = BinaryExpression(left=Identifier("with_context"), operator=BinaryOperator.PIPE, right=Identifier("without_context"))

    program = Program([Assignment(target=Identifier("local:f"), value=composition)])

    interpreter.execute_program(program, context)

    # Test the composed function
    composed_func = context.get("local:f")
    result = composed_func(context, 5)

    # Should be: with_context(5) = 10, without_context(10) = 20
    assert result == 20


def test_composed_function_with_complex_data():
    """Test composed functions that work with complex data structures"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that creates a person object
    def create_person(context, name):
        return {"name": name, "age": 0, "skills": []}

    # Function that adds age
    def set_age_25(context, person):
        person = person.copy()
        person["age"] = 25
        return person

    # Function that adds a skill
    def add_coding_skill(context, person):
        person = person.copy()
        person["skills"] = person["skills"] + ["coding"]
        return person

    interpreter.function_registry.register("create_person", create_person)
    interpreter.function_registry.register("set_age_25", set_age_25)
    interpreter.function_registry.register("add_coding_skill", add_coding_skill)

    # Create composition: person_builder = create_person | set_age_25 | add_coding_skill
    comp1 = BinaryExpression(left=Identifier("create_person"), operator=BinaryOperator.PIPE, right=Identifier("set_age_25"))

    comp2 = BinaryExpression(left=comp1, operator=BinaryOperator.PIPE, right=Identifier("add_coding_skill"))

    program = Program([Assignment(target=Identifier("local:person_builder"), value=comp2)])

    interpreter.execute_program(program, context)

    # Test the composed function
    person_builder = context.get("local:person_builder")
    result = person_builder(context, "Alice")

    assert result["name"] == "Alice"
    assert result["age"] == 25
    assert result["skills"] == ["coding"]


def test_composition_error_handling():
    """Test error handling in function composition"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that raises an error
    def error_func(context, x):
        raise ValueError(f"Error processing {x}")

    # Normal function
    def double(context, x):
        return x * 2

    interpreter.function_registry.register("error_func", error_func)
    interpreter.function_registry.register("double", double)

    # Create composition: f = double | error_func
    pipe1 = BinaryExpression(left=Identifier("double"), operator=BinaryOperator.PIPE, right=Identifier("error_func"))

    program = Program([Assignment(target=Identifier("local:f"), value=pipe1)])

    interpreter.execute_program(program, context)

    # Test that error is propagated correctly
    composed_func = context.get("local:f")

    with pytest.raises(Exception) as exc_info:
        composed_func(context, 5)

    assert "Error processing 10" in str(exc_info.value)


def test_composition_with_non_existent_function():
    """Test error handling when composing with non-existent functions"""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Register only one function
    def double(context, x):
        return x * 2

    interpreter.function_registry.register("double", double)

    # Try to compose with non-existent function: f = double | non_existent
    pipe1 = BinaryExpression(left=Identifier("double"), operator=BinaryOperator.PIPE, right=Identifier("non_existent"))

    program = Program([Assignment(target=Identifier("local:f"), value=pipe1)])

    # This should create the composition object (since we're not calling it yet)
    interpreter.execute_program(program, context)

    # But calling it should raise an error
    composed_func = context.get("local:f")

    with pytest.raises(Exception) as exc_info:
        composed_func(context, 5)

    assert "not found" in str(exc_info.value) or "not callable" in str(exc_info.value)
