"""
Mock parser for testing.

This module provides a simple mock parser for Dana that returns hardcoded AST nodes.
It is used in tests to bypass the actual parser when the grammar is not the focus
of the test.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from collections.abc import Sequence
from typing import Any

from dana.core.lang.ast import (
    Assignment,
    ExceptBlock,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    LiteralExpression,
    Parameter,
    Program,
    ReturnStatement,
    Statement,
    TryBlock,
)


def _create_function_call(name: str, args: dict[str, Any]) -> FunctionCall:
    """Create a function call node."""
    return FunctionCall(name=name, args=args, location=None)


def _create_assignment(name: str, value: Any) -> Assignment:
    """Create an assignment node."""
    return Assignment(target=Identifier(name=name), value=value, location=None)


def _create_function_def(name: str, params: list[str], body: Sequence[Statement]) -> FunctionDefinition:
    """Create a function definition node."""
    return FunctionDefinition(name=Identifier(name=name), parameters=[Parameter(name=p) for p in params], body=list(body), location=None)


def _parse_dana_logger(statements: list[Statement]) -> None:
    """Parse the dana_logger function from test_mixed_dana_and_python_functions."""
    body = [
        _create_assignment("result", _create_function_call("python_logger", {"message": Identifier(name="message")})),
        ReturnStatement(value=Identifier(name="result"), location=None),
    ]
    func_def = _create_function_def("dana_logger", ["message"], body)
    statements.append(func_def)


def _parse_format_and_log(statements: list[Statement]) -> None:
    """Parse the format_and_log function from test_mixed_dana_and_python_functions."""
    body = [
        _create_assignment("formatter", _create_function_call("create_formatter", {"format_type": Identifier(name="format_type")})),
        _create_assignment("formatted", _create_function_call("formatter", {"message": Identifier(name="message")})),
        ReturnStatement(value=_create_function_call("dana_logger", {"formatted": Identifier(name="formatted")}), location=None),
    ]
    func_def = _create_function_def("format_and_log", ["message", "format_type"], body)
    statements.append(func_def)


def _create_try_except_block() -> TryBlock:
    """Create a try/except block for the error handling test."""
    try_body: list[Statement] = [
        _create_assignment("result2", _create_function_call("divide", {"a": LiteralExpression(value=5), "b": LiteralExpression(value=0)}))
    ]
    except_body: list[Statement] = [_create_assignment("result2", LiteralExpression(value="Error caught"))]
    except_block = ExceptBlock(body=except_body, location=None)
    return TryBlock(body=try_body, except_blocks=[except_block], location=None)


def parse_program(text: str, do_type_check: bool = False) -> Program:
    """
    Mock implementation of parse_program for testing.

    This function recognizes specific test cases from test_end_to_end.py
    and returns appropriate AST nodes.

    Args:
        text: The program text to "parse"
        do_type_check: Ignored in the mock implementation

    Returns:
        Program AST node
    """
    statements: list[Statement] = []

    # Check which test case we're dealing with based on content
    if "dana_logger" in text and "format_and_log" in text:
        # test_mixed_dana_and_python_functions case
        _parse_dana_logger(statements)
        _parse_format_and_log(statements)

        # Add function calls
        statements.append(
            _create_assignment("log1", _create_function_call("dana_logger", {"message": LiteralExpression(value="Direct call")}))
        )
        statements.append(
            _create_assignment(
                "log2",
                _create_function_call(
                    "format_and_log", {"message": LiteralExpression(value="Indirect call"), "format_type": LiteralExpression(value="INFO")}
                ),
            )
        )

    elif "data = [1, 2, 3, 4, 5]" in text:
        # test_context_injection_with_type_annotations case
        statements.append(_create_assignment("data", LiteralExpression(value=[1, 2, 3, 4, 5])))
        statements.append(_create_assignment("result", _create_function_call("analyze_data", {"data": Identifier(name="data")})))

    elif "msg1 = format_message" in text:
        # test_keyword_and_positional_args case
        template1 = LiteralExpression(value="{name} is {age} years old from {location}")
        statements.append(
            _create_assignment(
                "msg1",
                _create_function_call(
                    "format_message",
                    {
                        "template": template1,
                        "name": LiteralExpression(value="Alice"),
                        "age": LiteralExpression(value=30),
                        "location": LiteralExpression(value="New York"),
                    },
                ),
            )
        )

        template2 = LiteralExpression(value="{name} is {age} years old from {location}")
        statements.append(
            _create_assignment(
                "msg2",
                _create_function_call(
                    "format_message",
                    {
                        "template": template2,
                        "name": LiteralExpression(value="Bob"),
                        "location": LiteralExpression(value="London"),
                        "age": LiteralExpression(value=25),
                    },
                ),
            )
        )

        template3 = LiteralExpression(value="{name} is from {location}")
        statements.append(
            _create_assignment(
                "msg3",
                _create_function_call(
                    "format_message",
                    {"template": template3, "name": LiteralExpression(value="Charlie"), "location": LiteralExpression(value="Paris")},
                ),
            )
        )

    elif "result1 = divide" in text:
        # test_error_handling case
        statements.append(
            _create_assignment(
                "result1", _create_function_call("divide", {"a": LiteralExpression(value=10), "b": LiteralExpression(value=2)})
            )
        )

        # Add try/except block
        statements.append(_create_try_except_block())

    # If no specific test case matched, return a default AST
    if not statements:
        statements.append(
            _create_assignment("result", _create_function_call("default_function", {"arg": LiteralExpression(value="default")}))
        )

    # Create the program
    program = Program(statements=statements, source_text=text)

    return program
