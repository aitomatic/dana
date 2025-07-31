"""
Functional tests for Dana's dual delivery mechanism in actual code.

Tests deliver (eager) and return (lazy) execution with real Dana programs.

Copyright © 2025 Aitomatic, Inc.
"""

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.dana_parser import parse_program
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.runtime.promise import is_promise


class TestDeliverReturnFunctional:
    """Functional tests for deliver and return statements in Dana code."""

    def test_deliver_eager_execution(self):
        """Test that deliver statements execute eagerly."""
        dana_code = """
def eager_function() -> int:
    deliver 42

result = eager_function()
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        # Should get concrete value immediately
        result = context.get("result")
        assert result == 42
        assert not is_promise(result)

    def test_return_lazy_execution(self):
        """Test that return statements create promises."""
        dana_code = """
def lazy_function() -> int:
    return 42

result = lazy_function()
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        # Should get Promise[T] wrapper
        result = context.get("result")
        assert is_promise(result)

        # Promise should resolve to correct value when accessed
        assert result == 42

    def test_deliver_with_computation(self):
        """Test deliver with complex computation."""
        dana_code = """
def compute_sum(a: int, b: int) -> int:
    deliver a + b

result = compute_sum(10, 20)
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        result = context.get("result")
        assert result == 30
        assert not is_promise(result)

    def test_return_with_computation(self):
        """Test return with complex computation."""
        dana_code = """
def lazy_compute_sum(a: int, b: int) -> int:
    return a + b

result = lazy_compute_sum(10, 20)
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        result = context.get("result")
        assert is_promise(result)
        assert result == 30  # Promise should resolve transparently

    def test_mixed_deliver_return_functions(self):
        """Test mixing deliver and return functions."""
        dana_code = """
def eager_double(x: int) -> int:
    deliver x * 2

def lazy_triple(x: int) -> int:
    return x * 3

eager_result = eager_double(5)
lazy_result = lazy_triple(5)
combined = eager_result + lazy_result
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        eager_result = context.get("eager_result")
        lazy_result = context.get("lazy_result")
        combined = context.get("combined")

        assert eager_result == 10
        assert not is_promise(eager_result)

        assert is_promise(lazy_result)
        assert lazy_result == 15

        assert combined == 25

    def test_promise_transparency_in_expressions(self):
        """Test that promises work transparently in complex expressions."""
        dana_code = """
def lazy_value() -> int:
    return 100

def another_lazy_value() -> int:
    return 50

# Promise[T] should work transparently in all operations
result1 = lazy_value() + another_lazy_value()
result2 = lazy_value() > another_lazy_value()
result3 = lazy_value() / 2
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        assert context.get("result1") == 150
        assert context.get("result2") is True
        assert context.get("result3") == 50.0

    def test_deliver_return_no_value(self):
        """Test deliver and return with no values."""
        dana_code = """
def eager_void():
    deliver

def lazy_void():
    return

eager_result = eager_void()
lazy_result = lazy_void()
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        assert context.get("eager_result") is None
        assert context.get("lazy_result") is None

    def test_conditional_execution_patterns(self):
        """Test deliver/return in conditional patterns."""
        dana_code = """
def conditional_execution(use_eager: bool) -> int:
    if use_eager:
        deliver 42
    else:
        return 24

eager_result = conditional_execution(True)
lazy_result = conditional_execution(False)
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        eager_result = context.get("eager_result")
        lazy_result = context.get("lazy_result")

        assert eager_result == 42
        assert not is_promise(eager_result)

        assert is_promise(lazy_result)
        assert lazy_result == 24

    def test_nested_function_calls(self):
        """Test deliver/return in nested function calls."""
        dana_code = """
def inner_eager() -> int:
    deliver 10

def inner_lazy() -> int:
    return 20

def outer_function() -> int:
    deliver inner_eager() + inner_lazy()

result = outer_function()
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        result = context.get("result")
        assert result == 30
        assert not is_promise(result)

    @pytest.mark.skip(reason="Multiple promise parallelization needs async context testing")
    def test_multiple_promise_parallelization(self):
        """Test that multiple promises are resolved in parallel."""
        dana_code = """
def slow_operation_a() -> int:
    return 10

def slow_operation_b() -> int:
    return 20

def slow_operation_c() -> int:
    return 30

# These should be resolved in parallel when accessed together
result = slow_operation_a() + slow_operation_b() + slow_operation_c()
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        result = context.get("result")
        assert result == 60

    def test_promise_error_handling(self):
        """Test error handling in promise resolution."""
        dana_code = """
def failing_function() -> int:
    return 1 / 0  # This will raise an error when resolved

problematic_result = failing_function()
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        problematic_result = context.get("problematic_result")
        assert is_promise(problematic_result)

        # Error should surface when promise is accessed
        with pytest.raises((ValueError, RuntimeError, Exception)):
            _ = problematic_result + 1

    def test_type_annotation_transparency(self):
        """Test that Promise[T] appears as T in type annotations."""
        dana_code = """
def lazy_string() -> str:
    return "hello"

def process_string(s: str) -> str:
    deliver s + " world"

# This should work - Promise[str] should appear as str
result = process_string(lazy_string())
"""
        # Parse and execute the Dana code
        program = parse_program(dana_code)
        context = SandboxContext()
        interpreter = DanaInterpreter()
        interpreter.execute_program(program, context)

        result = context.get("result")
        assert result == "hello world"
        assert not is_promise(result)


if __name__ == "__main__":
    pytest.main([__file__])
