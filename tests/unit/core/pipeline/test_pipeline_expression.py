"""
Tests for PipelineExpression functionality in Dana language.

Tests both implicit first-argument mode and explicit placeholder substitution mode
with the pipe operator (|) for function composition.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

import pytest

from dana.common.exceptions import SandboxError
from dana.core.lang.ast import FunctionCall, Identifier, LiteralExpression, PipelineExpression, PlaceholderExpression
from dana.core.lang.dana_sandbox import DanaSandbox
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
        pipeline = PipelineExpression(
            stages=[
                FunctionCall(name="add_prefix", args={"__positional": [LiteralExpression("Data: ")]}),
                FunctionCall(name="to_uppercase", args={"__positional": []}),
                FunctionCall(name="add_suffix", args={"__positional": [LiteralExpression("?")]}),
            ]
        )

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
        pipeline = PipelineExpression(
            stages=[
                FunctionCall(
                    name="format_message",
                    args={"__positional": [LiteralExpression("Start: "), PlaceholderExpression(), LiteralExpression(" :End")]},
                )
            ]
        )

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
        pipeline = PipelineExpression(
            stages=[
                FunctionCall(
                    name="combine_strings",
                    args={"__positional": [LiteralExpression("start"), PlaceholderExpression(), LiteralExpression("end")]},
                ),
                FunctionCall(name="add_prefix", args={"__positional": [LiteralExpression("result:")]}),
            ]
        )

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

        pipeline = PipelineExpression(
            stages=[
                FunctionCall(name="add_numbers", args={"__positional": [LiteralExpression(10)]}),
                FunctionCall(name="multiply_by", args={"__positional": [LiteralExpression(3)]}),
            ]
        )

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

        pipeline = PipelineExpression(
            stages=[
                FunctionCall(name="add_item", args={"__positional": [LiteralExpression("new")]}),
                FunctionCall(name="double_list", args={"__positional": []}),
            ]
        )

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

        pipeline = PipelineExpression(stages=[FunctionCall(name="echo_func", args={"__positional": []})])

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
        pipeline = PipelineExpression(
            stages=[FunctionCall(name="process_text", args={"__positional": [Identifier(name="upper_processor")]})]
        )

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("hello")
        assert result == "HELLO"

    def test_placeholder_expression_standalone_error(self):
        """Test that standalone placeholder expressions raise appropriate errors."""
        placeholder = PlaceholderExpression()

        with pytest.raises(SandboxError):  # Should raise SandboxError
            self.interpreter.evaluate_expression(placeholder, self.context)

    def test_complex_pipeline_with_multiple_placeholders(self):
        """Test complex pipeline with multiple placeholders in different positions."""

        def format_complex(prefix: str, middle: str, suffix: str, extra: str) -> str:
            return f"{prefix}[{middle}]{suffix}({extra})"

        def wrap_text(text: str, wrapper: str) -> str:
            return f"{wrapper}{text}{wrapper}"

        self.context.set("local:format_complex", format_complex)
        self.context.set("local:wrap_text", wrap_text)

        pipeline = PipelineExpression(
            stages=[
                FunctionCall(
                    name="format_complex",
                    args={
                        "__positional": [
                            LiteralExpression("start"),
                            PlaceholderExpression(),
                            LiteralExpression("end"),
                            LiteralExpression("extra"),
                        ]
                    },
                ),
                FunctionCall(name="wrap_text", args={"__positional": [LiteralExpression("*")]}),
            ]
        )

        composed = self.interpreter.evaluate_expression(pipeline, self.context)
        result = composed("middle")
        assert result == "*start[middle]end(extra)*"


class TestPipelineIntegration:
    """Test full integration of pipeline expressions in Dana code."""

    def setup_method(self):
        """Set up the interpreter and context for each test."""
        self.sandbox = DanaSandbox(debug_mode=True)
        self.context = self.sandbox.context

    def test_dana_code_implicit_mode(self):
        """Test implicit first argument mode in Dana code."""
        code = """
def add_prefix(text: str, prefix: str) -> str:
    return f"{prefix}{text}"

def to_uppercase(text: str) -> str:
    return text.upper()

def add_suffix(text: str, suffix: str) -> str:
    return f"{text}{suffix}"

# Create wrapper functions for the pipeline
def add_prefix_wrapper(text: str) -> str:
    return add_prefix(text, "DATA: ")

def add_suffix_wrapper(text: str) -> str:
    return add_suffix(text, "!")

# Create function composition pipeline
def pipeline(text: str) = add_prefix_wrapper | to_uppercase | add_suffix_wrapper
# Apply the composed function to data
result = pipeline("hello")
"""
        result = self.sandbox.execute_string(code)
        assert result.success
        assert result.final_context is not None
        result_value = result.final_context.get("result")
        assert result_value == "DATA: HELLO!"

    def test_dana_code_explicit_mode(self):
        """Test explicit placeholder mode in Dana code."""
        code = """
def wrap_text(text: str, left: str, right: str) -> str:
    return f"{left}{text}{right}"

def add_prefix(text: str, prefix: str) -> str:
    return f"{prefix}{text}"

# Create wrapper functions for the pipeline
def wrap_text_wrapper(text: str) -> str:
    return wrap_text(text, "(", ")")

def add_prefix_wrapper(text: str) -> str:
    return add_prefix(text, "wrapped: ")

# Create function composition pipeline
def pipeline(text: str) = wrap_text_wrapper | add_prefix_wrapper
# Apply the composed function to data
result = pipeline("world")
"""
        result = self.sandbox.execute_string(code)
        assert result.success
        assert result.final_context is not None
        result_value = result.final_context.get("result")
        assert result_value == "wrapped: (world)"
