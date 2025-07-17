"""
Tests for PipelineExpression functionality in Dana language.

Tests both implicit first-argument mode and explicit placeholder substitution mode
with the pipe operator (|) for function composition.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest
from typing import Any

from dana.core.lang.ast import PipelineExpression, PlaceholderExpression, FunctionCall, LiteralExpression, Identifier
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


class TestPipelineExpression:
    """Test suite for PipelineExpression functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

    def test_implicit_first_argument_mode(self):
        """Test implicit first argument mode where current value is inserted as first argument."""
        # Define test functions
        def add_prefix(text: str, prefix: str = "Prefix: ") -> str:
            return f"{prefix}{text}"

        def to_uppercase(text: str) -> str:
            return text.upper()

        def add_suffix(text: str, suffix: str = "!!!") -> str:
            return f"{text}{suffix}"

        # Register functions
        self.context.set("local:add_prefix", add_prefix)
        self.context.set("local:to_uppercase", to_uppercase)
        self.context.set("local:add_suffix", add_suffix)

        # Test basic pipeline
        pipeline = PipelineExpression(stages=[
            FunctionCall(name="add_prefix", args={"__positional": [LiteralExpression("Data: ")]}),
            FunctionCall(name="to_uppercase", args={"__positional": []}),
            FunctionCall(name="add_suffix", args={"__positional": [LiteralExpression("?")]})
        ])

        # The pipeline should return a callable
        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("hello")
        assert result == "DATA: HELLO?"

    def test_explicit_placeholder_mode(self):
        """Test explicit placeholder mode where $ determines substitution position."""
        def format_message(prefix: str, text: str, suffix: str) -> str:
            return f"{prefix}{text}{suffix}"

        def multiply_text(text: str, multiplier: int) -> str:
            return text * multiplier

        self.context.set("local:format_message", format_message)
        self.context.set("local:multiply_text", multiply_text)

        # Test middle placeholder
        pipeline = PipelineExpression(stages=[
            FunctionCall(name="format_message", args={
                "__positional": [
                    LiteralExpression("Start: "),
                    PlaceholderExpression(),
                    LiteralExpression(" :End")
                ]
            })
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("hello")
        assert result == "Start: hello :End"

    def test_mixed_modes(self):
        """Test mixing implicit and explicit modes in a pipeline."""
        def combine_strings(a: str, b: str, c: str) -> str:
            return f"{a}-{b}-{c}"

        def add_prefix(text: str, prefix: str) -> str:
            return f"{prefix}{text}"

        self.context.set("local:combine_strings", combine_strings)
        self.context.set("local:add_prefix", add_prefix)

        # Test: value | combine_strings("start", $, "end")
        pipeline = PipelineExpression(stages=[
            FunctionCall(name="combine_strings", args={
                "__positional": [
                    LiteralExpression("start"),
                    PlaceholderExpression(),
                    LiteralExpression("end")
                ]
            }),
            FunctionCall(name="add_prefix", args={
                "__positional": [LiteralExpression("result:")]
            })
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("middle")
        assert result == "result:start-middle-end"

    def test_numeric_operations(self):
        """Test pipeline with numeric operations."""
        def add_numbers(a: int, b: int) -> int:
            return a + b

        def multiply_by(a: int, multiplier: int) -> int:
            return a * multiplier

        self.context.set("local:add_numbers", add_numbers)
        self.context.set("local:multiply_by", multiply_by)

        pipeline = PipelineExpression(stages=[
            FunctionCall(name="add_numbers", args={"__positional": [LiteralExpression(10)]}),
            FunctionCall(name="multiply_by", args={"__positional": [LiteralExpression(3)]})
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed(5)
        assert result == 45  # (5 + 10) * 3

    def test_list_operations(self):
        """Test pipeline with list operations."""
        def add_item(lst: list, item: Any) -> list:
            return lst + [item]

        def double_list(lst: list) -> list:
            return lst * 2

        self.context.set("local:add_item", add_item)
        self.context.set("local:double_list", double_list)

        pipeline = PipelineExpression(stages=[
            FunctionCall(name="add_item", args={"__positional": [LiteralExpression("new")]}),
            FunctionCall(name="double_list", args={"__positional": []})
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed([1, 2, 3])
        assert result == [1, 2, 3, "new", 1, 2, 3, "new"]

    def test_empty_pipeline(self):
        """Test empty pipeline behavior."""
        pipeline = PipelineExpression(stages=[])
        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("test")
        assert result == "test"  # Should return input unchanged

    def test_single_stage_pipeline(self):
        """Test pipeline with single stage."""
        def echo_func(text: str) -> str:
            return f"echo: {text}"

        self.context.set("local:echo_func", echo_func)

        pipeline = PipelineExpression(stages=[
            FunctionCall(name="echo_func", args={"__positional": []})
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("hello")
        assert result == "echo: hello"

    def test_nested_function_calls(self):
        """Test pipeline with nested function calls as stages."""
        def process_text(text: str, processor: Any) -> str:
            return processor(text)

        def upper_processor(text: str) -> str:
            return text.upper()

        self.context.set("local:process_text", process_text)
        self.context.set("local:upper_processor", upper_processor)

        # This tests that we can use the result of one stage as a function in another
        pipeline = PipelineExpression(stages=[
            FunctionCall(name="process_text", args={
                "__positional": [Identifier(name="upper_processor")]
            })
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("hello")
        assert result == "HELLO"

    def test_placeholder_expression_standalone_error(self):
        """Test that standalone placeholder expressions raise appropriate errors."""
        placeholder = PlaceholderExpression()

        with pytest.raises(Exception):  # Should raise SandboxError
            self.interpreter.evaluate_expression(placeholder, self.context)

    def test_complex_pipeline_with_multiple_placeholders(self):
        """Test complex pipeline with multiple placeholders in different positions."""
        def format_complex(prefix: str, middle: str, suffix: str, extra: str) -> str:
            return f"{prefix}[{middle}]{suffix}({extra})"

        def wrap_text(text: str, wrapper: str) -> str:
            return f"{wrapper}{text}{wrapper}"

        self.context.set("local:format_complex", format_complex)
        self.context.set("local:wrap_text", wrap_text)

        pipeline = PipelineExpression(stages=[
            FunctionCall(name="format_complex", args={
                "__positional": [
                    LiteralExpression("start"),
                    PlaceholderExpression(),
                    LiteralExpression("end"),
                    LiteralExpression("extra")
                ]
            }),
            FunctionCall(name="wrap_text", args={
                "__positional": [LiteralExpression("*")]
            })
        ])

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("middle")
        assert result == "*start[middle]end(extra)*"


class TestPipelineIntegration:
    """Integration tests for PipelineExpression with actual Dana code."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()

    def test_dana_code_implicit_mode(self):
        """Test implicit mode using actual Dana code."""
        code = '''
def add_prefix(text: str, prefix: str = "Prefix: ") -> str:
    return f"{prefix}{text}"

def to_uppercase(text: str) -> str:
    return text.upper()

result = "hello" | add_prefix("Data: ") | to_uppercase
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == "DATA: HELLO"

    def test_dana_code_explicit_mode(self):
        """Test explicit mode using actual Dana code."""
        code = '''
def format_message(prefix: str, text: str, suffix: str) -> str:
    return f"{prefix}{text}{suffix}"

result = "world" | format_message("(", $, ")")
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == "(world)"

    def test_dana_code_numeric_operations(self):
        """Test numeric operations in pipeline."""
        code = '''
def add_numbers(a: int, b: int) -> int:
    return a + b

def multiply_by(a: int, multiplier: int) -> int:
    return a * multiplier

result = 5 | add_numbers(10) | multiply_by(2)
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == 30  # (5 + 10) * 2