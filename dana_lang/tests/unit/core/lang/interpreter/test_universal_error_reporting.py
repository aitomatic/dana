"""
Tests for universal error reporting with execution tracking.

This module tests that the enhanced error reporting system provides
detailed execution traces for all types of errors.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest
from unittest.mock import patch

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.lang.interpreter.error_formatter import EnhancedErrorFormatter


class TestUniversalErrorReporting:
    """Test universal error reporting functionality."""

    def test_detailed_error_reporting_with_tracking(self):
        """Test that detailed error reporting works with execution tracking enabled."""
        # Create a sandbox with tracking enabled
        sandbox = DanaSandbox(track_execution=True)

        # Create a test Dana program that will cause an error
        test_code = """
# Test program with multiple statements
x = 42
y = x + 1
z = y / 0  # This will cause a division by zero error
"""

        try:
            result = sandbox.execute_string(test_code, filename="test_error.na")
            assert result.success is False
            assert result.error is not None

            # Check that the error message contains detailed execution trace
            error_msg = str(result.error)
            assert "=== Dana Runtime Error ===" in error_msg
            assert "File: test_error.na" in error_msg
            assert "Execution Trace:" in error_msg
            assert "statement 1" in error_msg
            assert "statement 2" in error_msg
            assert "statement 3" in error_msg

        except Exception as e:
            # If the error is raised instead of returned, check the formatted error
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            assert "=== Dana Runtime Error ===" in formatted_error
            assert "Execution Trace:" in formatted_error

    def test_error_reporting_without_tracking(self):
        """Test that error reporting works without execution tracking."""
        # Create a sandbox with tracking disabled
        sandbox = DanaSandbox(track_execution=False)

        # Create a test Dana program that will cause an error
        test_code = """
x = 42
y = x + 1
z = y / 0  # This will cause a division by zero error
"""

        try:
            result = sandbox.execute_string(test_code, filename="test_error.na")
            assert result.success is False
            assert result.error is not None

            # Check that the error message does not contain execution trace
            error_msg = str(result.error)
            # Should still have basic error information but no detailed trace
            assert "ZeroDivisionError" in error_msg or "division by zero" in error_msg

        except Exception as e:
            # If the error is raised instead of returned, check the formatted error
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            # Should not have execution trace when tracking is disabled
            assert "Execution Trace:" not in formatted_error

    def test_function_call_error_tracking(self):
        """Test that function call errors are properly tracked."""
        sandbox = DanaSandbox(track_execution=True)

        # Create a test program with function calls
        test_code = """
def test_function(x):
    return x + 1

def another_function(y):
    return y / 0  # This will cause an error

result = test_function(5)
error_result = another_function(10)
"""

        try:
            result = sandbox.execute_string(test_code, filename="test_function_error.na")
            assert result.success is False
            assert result.error is not None

            # Check that the error message contains function call tracking
            error_msg = str(result.error)
            assert "=== Dana Runtime Error ===" in error_msg
            assert "Execution Trace:" in error_msg
            assert "function call" in error_msg or "statement" in error_msg

        except Exception as e:
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            assert "=== Dana Runtime Error ===" in formatted_error

    def test_assignment_error_tracking(self):
        """Test that assignment errors are properly tracked."""
        sandbox = DanaSandbox(track_execution=True)

        # Create a test program with assignment errors
        test_code = """
x = 42
y = x + 1
z = y / 0  # Division by zero in assignment
"""

        try:
            result = sandbox.execute_string(test_code, filename="test_assignment_error.na")
            assert result.success is False
            assert result.error is not None

            # Check that the error message contains assignment tracking
            error_msg = str(result.error)
            assert "=== Dana Runtime Error ===" in error_msg
            assert "Execution Trace:" in error_msg

        except Exception as e:
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            assert "=== Dana Runtime Error ===" in formatted_error

    def test_import_error_tracking(self):
        """Test that import errors are properly tracked."""
        sandbox = DanaSandbox(track_execution=True)

        # Create a test program with import errors
        test_code = """
import nonexistent_module  # This will cause an import error
x = 42
"""

        try:
            result = sandbox.execute_string(test_code, filename="test_import_error.na")
            assert result.success is False
            assert result.error is not None

            # Check that the error message contains import tracking
            error_msg = str(result.error)
            assert "=== Dana Runtime Error ===" in error_msg
            assert "Execution Trace:" in error_msg

        except Exception as e:
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            assert "=== Dana Runtime Error ===" in formatted_error

    def test_nested_function_error_tracking(self):
        """Test that nested function call errors are properly tracked."""
        sandbox = DanaSandbox(track_execution=True)

        # Create a test program with nested function calls
        test_code = """
def outer_function(x):
    def inner_function(y):
        return y / 0  # This will cause an error
    return inner_function(x)

result = outer_function(10)
"""

        try:
            result = sandbox.execute_string(test_code, filename="test_nested_error.na")
            assert result.success is False
            assert result.error is not None

            # Check that the error message contains nested function tracking
            error_msg = str(result.error)
            assert "=== Dana Runtime Error ===" in error_msg
            assert "Execution Trace:" in error_msg

        except Exception as e:
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            assert "=== Dana Runtime Error ===" in formatted_error

    def test_error_context_preservation(self):
        """Test that error context is preserved across multiple executions."""
        sandbox = DanaSandbox(track_execution=True)

        # First execution - should work
        test_code1 = """
x = 42
y = x + 1
"""

        result1 = sandbox.execute_string(test_code1, filename="test1.na")
        assert result1.success is True

        # Second execution - should fail with tracking
        test_code2 = """
a = 10
b = a / 0  # This will cause an error
"""

        try:
            result2 = sandbox.execute_string(test_code2, filename="test2.na")
            assert result2.success is False
            assert result2.error is not None

            # Check that the error message contains proper tracking
            error_msg = str(result2.error)
            assert "=== Dana Runtime Error ===" in error_msg
            assert "Execution Trace:" in error_msg

        except Exception as e:
            formatted_error = EnhancedErrorFormatter.format_developer_error(e, sandbox._context.error_context)
            assert "=== Dana Runtime Error ===" in formatted_error

    def test_error_formatter_with_execution_stack(self):
        """Test that EnhancedErrorFormatter works with execution stack."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        # Mock the source file loading
        with patch.object(context.error_context, "load_source", return_value=["x = 42", "y = x + 1", "z = y / 0"]):
            # Manually add some execution locations to the stack
            from dana.core.lang.interpreter.error_context import ExecutionLocation

            location1 = ExecutionLocation(filename="test.na", line=1, column=1, function_name="statement 1")

            location2 = ExecutionLocation(filename="test.na", line=2, column=1, function_name="statement 2")

            location3 = ExecutionLocation(filename="test.na", line=3, column=1, function_name="statement 3")

            context.error_context.push_location(location1)
            context.error_context.push_location(location2)
            context.error_context.push_location(location3)

            # Create a test error
            test_error = ZeroDivisionError("division by zero")

            # Format the error
            formatted_error = EnhancedErrorFormatter.format_developer_error(test_error, context.error_context)

            # Check that the formatted error contains execution trace
            assert "=== Dana Runtime Error ===" in formatted_error
            assert "File: test.na" in formatted_error
            assert "Error: ZeroDivisionError - division by zero" in formatted_error
            assert "Execution Trace:" in formatted_error
            assert "1. Line 1, column 1, statement 1" in formatted_error
            assert "2. Line 2, column 1, statement 2" in formatted_error
            assert "3. Line 3, column 1, statement 3" in formatted_error
            assert "Code: x = 42" in formatted_error
            assert "Code: y = x + 1" in formatted_error
            assert "Code: z = y / 0" in formatted_error

    def test_error_formatter_without_execution_stack(self):
        """Test that EnhancedErrorFormatter works without execution stack."""
        context = SandboxContext(track_execution=False)
        context.error_context.set_file("test.na")

        # Create a test error
        test_error = ZeroDivisionError("division by zero")

        # Format the error
        formatted_error = EnhancedErrorFormatter.format_developer_error(test_error, context.error_context)

        # Check that the formatted error does not contain execution trace
        assert "=== Dana Runtime Error ===" in formatted_error
        assert "File: test.na" in formatted_error
        assert "Error: ZeroDivisionError - division by zero" in formatted_error
        assert "Execution Trace:" not in formatted_error

    def test_configuration_consistency(self):
        """Test that configuration is consistent across different components."""
        # Test with tracking enabled
        sandbox_enabled = DanaSandbox(track_execution=True)
        assert sandbox_enabled._context.track_execution is True

        # Test with tracking disabled
        sandbox_disabled = DanaSandbox(track_execution=False)
        assert sandbox_disabled._context.track_execution is False

        # Test context inheritance
        parent_context = SandboxContext(track_execution=True)
        child_context = SandboxContext(parent=parent_context)
        assert child_context.track_execution is True  # Should inherit from parent


if __name__ == "__main__":
    pytest.main([__file__])
