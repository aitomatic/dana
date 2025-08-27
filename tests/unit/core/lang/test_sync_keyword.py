"""
Unit tests for sync keyword functionality in Dana language.

Tests the sync keyword that allows functions to execute synchronously,
bypassing the automatic concurrency system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from unittest.mock import patch

import pytest

from dana.core.concurrency import is_promise
from dana.core.lang.interpreter.functions.dana_function import DanaFunction
from dana.core.lang.sandbox_context import SandboxContext


class TestSyncKeyword:
    """Test sync keyword functionality."""

    @pytest.fixture
    def context(self):
        """Create a sandbox context for testing."""
        return SandboxContext()

    def test_sync_function_definition(self, context):
        """Test that sync functions are parsed and created correctly."""
        source = """sync def simple_function():
    return 42
"""

        # Parse and execute the source
        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        _result = interpreter.execute_program_string(source, context)

        # Get the function from context
        func = context.get("simple_function")
        assert func is not None
        assert isinstance(func, DanaFunction)
        assert func.is_sync is True
        assert func.__name__ == "simple_function"

    def test_sync_function_execution(self, context):
        """Test that sync functions execute synchronously."""
        source = """sync def sync_func():
    return "sync result"

result = sync_func()
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        # Check that the result is not a promise
        result = context.get("result")
        assert not is_promise(result)
        assert result == "sync result"

    def test_async_function_default(self, context):
        """Test that regular functions default to async behavior."""
        source = """def async_func():
    return "async result"

result = async_func()
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        # Check that the result is auto-resolved to the expected value
        # (Promises are auto-resolved when retrieved from context)
        result = context.get("result")
        assert result == "async result"

        # Verify that the function itself is not sync
        func = context.get("async_func")
        assert func.is_sync is False

    def test_sync_function_with_parameters(self, context):
        """Test sync functions with parameters."""
        source = """sync def add(a, b):
    return a + b

result = add(5, 3)
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        result = context.get("result")
        assert not is_promise(result)
        assert result == 8

    def test_sync_function_with_return_type(self, context):
        """Test sync functions with return type annotations."""
        source = """sync def get_value() -> int:
    return 42

result = get_value()
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        result = context.get("result")
        assert not is_promise(result)
        assert result == 42

    def test_sync_function_in_conditional(self, context):
        """Test sync functions used in conditional statements."""
        source = """sync def is_positive(n):
    return n > 0

result1 = is_positive(5)
result2 = is_positive(-3)
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        result1 = context.get("result1")
        result2 = context.get("result2")
        assert not is_promise(result1)
        assert not is_promise(result2)
        assert result1 is True
        assert result2 is False

    def test_sync_function_recursion(self, context):
        """Test sync functions with recursion."""
        source = """sync def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        result = context.get("result")
        assert not is_promise(result)
        assert result == 120

    def test_sync_function_with_promise_limiter(self, context):
        """Test that sync functions bypass the promise limiter."""
        source = """sync def sync_operation():
    return "sync done"

result = sync_operation()
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()

        # Mock the promise limiter to verify it's not used for sync functions
        with patch("dana.core.concurrency.promise_limiter.PromiseLimiter.create_promise") as mock_create:
            interpreter.execute_program_string(source, context)

            # The promise limiter should not be called for sync functions
            mock_create.assert_not_called()

        result = context.get("result")
        assert not is_promise(result)
        assert result == "sync done"

    def test_sync_function_backward_compatibility(self, context):
        """Test that existing code without sync keyword still works."""
        source = """def existing_func():
    return "existing"

result = existing_func()
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        # Regular functions should still be async by default (auto-resolved)
        result = context.get("result")
        assert result == "existing"

        # Verify that the function itself is not sync
        func = context.get("existing_func")
        assert func.is_sync is False

    def test_mixed_sync_and_async_functions(self, context):
        """Test mixing sync and async functions in the same program."""
        source = """sync def sync_func():
    return "sync"

def async_func():
    return "async"

sync_result = sync_func()
async_result = async_func()
"""

        from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter

        interpreter = DanaInterpreter()
        interpreter.execute_program_string(source, context)

        sync_result = context.get("sync_result")
        async_result = context.get("async_result")

        # Sync functions return direct results
        assert sync_result == "sync"

        # Async functions return auto-resolved results (Promises are auto-resolved)
        assert async_result == "async"

        # Verify function types
        sync_func = context.get("sync_func")
        async_func = context.get("async_func")
        assert sync_func.is_sync is True
        assert async_func.is_sync is False
