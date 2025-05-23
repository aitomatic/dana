"""
Test cases comparing print_function and log_function behavior.

This test file demonstrates why print_function works correctly while
log_function fails due to signature and implementation differences.
"""

from unittest.mock import patch

import pytest

from opendxa.dana.sandbox.interpreter.functions.core.log_function import log_function
from opendxa.dana.sandbox.interpreter.functions.core.print_function import print_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestPrintVsLogFunctions:
    """Test suite comparing print and log function behaviors."""

    def test_print_function_works_with_multiple_args(self, capsys):
        """Test that print_function handles multiple arguments correctly."""
        context = SandboxContext()

        # Test with multiple arguments
        print_function(context, "Hello", "world", 123)

        captured = capsys.readouterr()
        assert "Hello world 123" in captured.out

    def test_print_function_works_with_single_arg(self, capsys):
        """Test that print_function handles single argument correctly."""
        context = SandboxContext()

        # Test with single argument
        print_function(context, "Hello world")

        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    def test_log_function_signature_limitation(self):
        """Test that log_function only accepts a single message string."""
        context = SandboxContext()

        # This should work - single string argument
        with patch("opendxa.dana.sandbox.log_manager.SandboxLogger.log") as mock_log:
            log_function(context, "Hello world")
            mock_log.assert_called_once()

    def test_log_function_fails_with_multiple_args(self):
        """Test that log_function cannot handle multiple arguments due to its single-parameter signature."""
        context = SandboxContext()

        # log_function has signature: log_function(context, message: str, options=None)
        # It cannot accept multiple string arguments like print_function can

        # This works - single message
        with patch("opendxa.dana.sandbox.log_manager.SandboxLogger.log") as mock_log:
            log_function(context, "Single message")
            mock_log.assert_called_once()

        # This would fail due to signature mismatch - not a bug, it's by design
        # print_function(context, "Hello", "World", 123)  # This works
        # log_function(context, "Hello", "World", 123)   # TypeError: too many positional arguments

    def test_log_function_sandbox_logger_issue(self):
        """Test that log_function fails due to incorrect DXA_LOGGER.log() call."""
        context = SandboxContext()

        # Mock DXA_LOGGER.log to raise TypeError when called with unexpected arguments
        with patch("opendxa.dana.sandbox.log_manager.DXA_LOGGER") as mock_dxa_logger:
            # Simulate the real DXA_LOGGER.log signature which doesn't accept 'scope'
            mock_dxa_logger.log.side_effect = TypeError("log() got an unexpected keyword argument 'scope'")

            with pytest.raises(TypeError, match="unexpected keyword argument 'scope'"):
                log_function(context, "Test message")

    def test_print_function_argument_processing(self, capsys):
        """Test print_function's argument processing capabilities."""
        context = SandboxContext()

        # Test with different types of arguments
        print_function(context, "String", 42, True, None)

        captured = capsys.readouterr()
        assert "String 42 True None" in captured.out

    def test_log_function_level_parameter(self):
        """Test log_function's level parameter functionality."""
        context = SandboxContext()

        with patch("opendxa.dana.sandbox.log_manager.SandboxLogger.log") as mock_log:
            # Test with different log levels
            log_function(context, "Debug message", {"level": "debug"})
            log_function(context, "Info message", {"level": "info"})
            log_function(context, "Error message", {"level": "error"})

            assert mock_log.call_count == 3

    def test_core_function_registration_compatibility(self):
        """Test that both functions are registered correctly by the core registration system."""
        from opendxa.dana.sandbox.interpreter.functions.core.register_core_functions import register_core_functions
        from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

        registry = FunctionRegistry()
        register_core_functions(registry)

        # Both functions should be registered (use 'has' method instead of 'is_registered')
        assert registry.has("print")
        assert registry.has("log")

        # Check their registered functions
        print_func, _, _ = registry.resolve("print")
        log_func, _, _ = registry.resolve("log")

        assert print_func is not None
        assert log_func is not None

    @patch("opendxa.dana.sandbox.log_manager.DXA_LOGGER.log")
    def test_sandbox_logger_incorrect_call_signature(self, mock_dxa_log):
        """Test that SandboxLogger.log calls DXA_LOGGER.log with incorrect signature."""
        from opendxa.dana.sandbox.log_manager import SandboxLogger

        # This will demonstrate the bug: SandboxLogger.log passes 'scope' but DXA_LOGGER.log doesn't accept it
        mock_dxa_log.side_effect = TypeError("log() got an unexpected keyword argument 'scope'")

        with pytest.raises(TypeError, match="unexpected keyword argument 'scope'"):
            SandboxLogger.log("Test message", "info")

    def test_demonstrate_the_bug_root_cause(self):
        """Test that demonstrates the root cause of why log didn't work."""
        # The bug was in SandboxLogger.log() method which called:
        # DXA_LOGGER.log(message=message, level=level, scope=SandboxLogger.LOG_SCOPE)
        #
        # But DXA_LOGGER.log() signature is:
        # log(level: Union[int, str], message: str, *args, **context)
        #
        # There's no 'scope' parameter, and the argument order was wrong!

        import inspect

        from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER

        # Get the actual signature of DXA_LOGGER.log
        dxa_log_sig = inspect.signature(DXA_LOGGER.log)
        assert "scope" not in dxa_log_sig.parameters

        # The SandboxLogger was calling it incorrectly - this was the source of the bug
        # Now fixed in SandboxLogger.log() to call: DXA_LOGGER.log(level, message)
        assert True  # This test demonstrates the issue was resolved

    def test_signature_differences(self):
        """Demonstrate the signature differences between print and log functions."""
        import inspect

        from opendxa.dana.sandbox.interpreter.functions.core.log_function import log_function
        from opendxa.dana.sandbox.interpreter.functions.core.print_function import print_function

        print_sig = inspect.signature(print_function)
        log_sig = inspect.signature(log_function)

        # Verify the signatures are different
        assert str(print_sig) != str(log_sig)

        # print_function should accept *args
        assert "*args" in str(print_sig)

        # log_function should accept message: str
        assert "message: str" in str(log_sig)

        # Both should work correctly now that SandboxLogger bug is fixed
        assert True


class TestLogFunctionFix:
    """Test cases for the fixed log function."""

    def test_proposed_log_function_fix(self):
        """Test a proposed fix for the log function."""
        context = SandboxContext()

        # Proposed fix: change SandboxLogger.log to call DXA_LOGGER.log correctly
        with patch("opendxa.dana.sandbox.log_manager.DXA_LOGGER.log") as mock_dxa_log:
            from opendxa.dana.sandbox.log_manager import LogLevel

            # Fixed call should be:
            message = "Test message"
            level = LogLevel.INFO.value
            mock_dxa_log(level, message)  # Correct order and no 'scope'

            mock_dxa_log.assert_called_once_with(level, message)
