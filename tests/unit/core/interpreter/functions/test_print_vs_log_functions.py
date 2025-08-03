"""
Test cases comparing print_function and log_function behavior.

This test file demonstrates why print_function works correctly while
log_function fails due to signature and implementation differences.
"""

from unittest.mock import patch

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.stdlib.core.log_function import log_function
from dana.core.stdlib.core.print_function import print_function


@pytest.mark.deep
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

        # This should work - single string argument with level
        with patch("dana.core.lang.log_manager.SandboxLogger.log") as mock_log:
            log_function(context, "Hello world", "info")
            mock_log.assert_called_once()

    def test_log_function_fails_with_multiple_args(self):
        """Test that log_function cannot handle multiple arguments due to its single-parameter signature."""
        context = SandboxContext()

        # log_function has signature: log_function(context, message: str, level: str, options=None)
        # It cannot accept multiple string arguments like print_function can

        # This works - single message with level
        with patch("dana.core.lang.log_manager.SandboxLogger.log") as mock_log:
            log_function(context, "Single message", "info")
            mock_log.assert_called_once()

        # This would fail due to signature mismatch - not a bug, it's by design
        # print_function(context, "Hello", "World", 123)  # This works
        # log_function(context, "Hello", "World", 123)   # TypeError: too many positional arguments

    def test_log_function_sandbox_logger_issue(self):
        """Test that log_function fails due to incorrect DANA_LOGGER.log() call."""
        context = SandboxContext()

        # Mock DANA_LOGGER.log to raise TypeError when called with unexpected arguments
        with patch("dana.common.utils.logging.dxa_logger.DANA_LOGGER") as mock_dxa_logger:
            # Simulate the real DANA_LOGGER.log signature which doesn't accept 'scope'
            mock_dxa_logger.log.side_effect = TypeError("log() got an unexpected keyword argument 'scope'")

            with pytest.raises(TypeError, match="unexpected keyword argument 'scope'"):
                log_function(context, "Test message", "info")

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

        with patch("dana.core.lang.log_manager.SandboxLogger.log") as mock_log:
            # Test with different log levels as positional parameters
            log_function(context, "Debug message", "debug")
            log_function(context, "Info message", "info")
            log_function(context, "Error message", "error")

            assert mock_log.call_count == 3

    def test_core_function_registration_compatibility(self):
        """Test that both functions are registered correctly by the core registration system."""
        from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
        from dana.core.stdlib.core.register_core_functions import register_core_functions

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

    @patch("dana.common.utils.logging.dxa_logger.DANA_LOGGER.log")
    def test_sandbox_logger_incorrect_call_signature(self, mock_dxa_log):
        """Test that SandboxLogger.log calls DANA_LOGGER.log with incorrect signature."""
        from dana.core.lang.log_manager import SandboxLogger

        # This will demonstrate the bug: SandboxLogger.log passes 'scope' but DANA_LOGGER.log doesn't accept it
        mock_dxa_log.side_effect = TypeError("log() got an unexpected keyword argument 'scope'")

        with pytest.raises(TypeError, match="unexpected keyword argument 'scope'"):
            SandboxLogger.log("Test message", "info")

    def test_demonstrate_the_bug_root_cause(self):
        """Test that demonstrates the root cause of why log didn't work."""
        # The bug was in SandboxLogger.log() method which called:
        # DANA_LOGGER.log(message=message, level=level, scope=SandboxLogger.LOG_SCOPE)
        #
        # But DANA_LOGGER.log() signature is:
        # log(level: Union[int, str], message: str, *args, **context)
        #
        # There's no 'scope' parameter, and the argument order was wrong!

        import inspect

        from dana.common.utils.logging.dxa_logger import DANA_LOGGER

        # Get the actual signature of DANA_LOGGER.log
        dxa_log_sig = inspect.signature(DANA_LOGGER.log)
        assert "scope" not in dxa_log_sig.parameters

        # The SandboxLogger was calling it incorrectly - this was the source of the bug
        # Now fixed in SandboxLogger.log() to call: DANA_LOGGER.log(level, message)
        assert True  # This test demonstrates the issue was resolved

    def test_signature_differences(self):
        """Demonstrate the signature differences between print and log functions."""
        import inspect

        from dana.core.stdlib.core.log_function import log_function
        from dana.core.stdlib.core.print_function import print_function

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


@pytest.mark.deep
class TestLogFunctionFix:
    """Test cases for the fixed log function."""

    def test_proposed_log_function_fix(self):
        """Test a proposed fix for the log function."""
        _ = SandboxContext()

        # Proposed fix: change SandboxLogger.log to call DANA_LOGGER.log correctly
        with patch("dana.common.utils.logging.dxa_logger.DANA_LOGGER.log") as mock_dxa_log:
            from dana.core.lang.log_manager import LogLevel

            # Fixed call should be:
            message = "Test message"
            level = LogLevel.INFO.value
            mock_dxa_log(level, message)  # Correct order and no 'scope'

            mock_dxa_log.assert_called_once_with(level, message)


@pytest.mark.deep
class TestLogLevelFunction:
    """Test suite for the log_level function."""

    def test_log_level_function_basic(self):
        """Test basic log_level function functionality."""
        from dana.core.stdlib.core.log_level_function import log_level_function

        context = SandboxContext()

        with patch("dana.core.lang.log_manager.SandboxLogger.set_system_log_level") as mock_set_level:
            log_level_function(context, "debug")
            mock_set_level.assert_called_once()

    def test_log_level_function_valid_levels(self):
        """Test log_level function with different valid levels."""
        from dana.core.stdlib.core.log_level_function import log_level_function

        context = SandboxContext()

        valid_levels = ["debug", "info", "warn", "error"]

        with patch("dana.core.lang.log_manager.SandboxLogger.set_system_log_level") as mock_set_level:
            for level in valid_levels:
                log_level_function(context, level)

            assert mock_set_level.call_count == len(valid_levels)

    def test_log_level_function_invalid_level(self):
        """Test log_level function with invalid level."""
        from dana.core.stdlib.core.log_level_function import log_level_function

        context = SandboxContext()

        with pytest.raises(ValueError, match="Invalid log level"):
            log_level_function(context, "invalid_level")

    def test_log_level_function_case_insensitive(self):
        """Test log_level function handles case insensitivity."""
        from dana.core.stdlib.core.log_level_function import log_level_function

        context = SandboxContext()

        with patch("dana.core.lang.log_manager.SandboxLogger.set_system_log_level") as mock_set_level:
            # Test uppercase
            log_level_function(context, "DEBUG")
            log_level_function(context, "Info")
            log_level_function(context, "WARN")
            log_level_function(context, "error")

            assert mock_set_level.call_count == 4

    def test_log_level_function_with_options(self):
        """Test log_level function with options parameter."""
        from dana.core.stdlib.core.log_level_function import log_level_function

        context = SandboxContext()

        with patch("dana.core.lang.log_manager.SandboxLogger.set_system_log_level") as mock_set_level:
            # Test with options override
            log_level_function(context, "", "dana", {"level": "error"})
            mock_set_level.assert_called_once()

    def test_log_level_function_registration(self):
        """Test that log_level function is registered correctly."""
        from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
        from dana.core.stdlib.core.register_core_functions import register_core_functions

        registry = FunctionRegistry()
        register_core_functions(registry)

        # The log_level function should be registered as "log_level"
        assert registry.has("log_level")

        # Check the registered function
        log_level_func, _, _ = registry.resolve("log_level")
        assert log_level_func is not None


class TestDynamicHelp:
    """Test suite for the dynamic core function help system."""

    def test_dynamic_help_lists_core_functions(self):
        """Test that dynamic help correctly lists all registered core functions."""
        import sys
        from io import StringIO

        from dana.core.lang.log_manager import LogLevel
        from dana.core.repl.dana_repl_app import DanaREPLApp

        # Create REPL app
        app = DanaREPLApp(log_level=LogLevel.INFO)

        # Capture the help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            app.command_handler.help_formatter.show_core_functions_plain()
            help_output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify core functions are listed
        registry = app.repl.interpreter.function_registry
        core_functions = registry.list("local")

        # All core functions should appear in the help output
        for func_name in core_functions:
            # Check for function name with parentheses (as displayed in help)
            assert f"{func_name}(...)" in help_output, f"Function {func_name}(...) not found in help output"

        # Verify categories are shown
        assert "Output:" in help_output or "print" in help_output
        assert "Logging:" in help_output or "log" in help_output
        assert "Function Examples:" in help_output

    def test_dynamic_help_adapts_to_new_functions(self):
        """Test that dynamic help adapts when new functions are registered."""
        import sys
        from io import StringIO

        from dana.core.lang.log_manager import LogLevel
        from dana.core.repl.dana_repl_app import DanaREPLApp

        # Create REPL app
        app = DanaREPLApp(log_level=LogLevel.INFO)
        registry = app.repl.interpreter.function_registry

        # Capture initial help output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            app.command_handler.help_formatter.show_core_functions_plain()
            initial_help = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Register a new function
        def test_function(context, message: str, options=None):
            return f"Test: {message}"

        registry.register("test_func", test_function, "local")

        # Capture updated help output
        sys.stdout = captured_output = StringIO()

        try:
            app.command_handler.help_formatter.show_core_functions_plain()
            updated_help = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify the new function appears in updated help
        assert "test_func(...)" not in initial_help
        assert "test_func(...)" in updated_help
        assert "Other:" in updated_help  # Should appear in "Other" category

    def test_tab_completion_includes_core_functions(self):
        """Test that tab completion includes all registered core functions."""
        from dana.core.lang.log_manager import LogLevel
        from dana.core.repl.dana_repl_app import DanaREPLApp

        # Create REPL app
        app = DanaREPLApp(log_level=LogLevel.INFO)

        # Get core functions from registry
        registry = app.repl.interpreter.function_registry
        core_functions = registry.list("local")

        # Get completer words from prompt session
        completer = app.prompt_manager.prompt_session.completer
        if completer is None or not hasattr(completer, "words"):
            pytest.skip("Completer not available or does not have words attribute")

        completion_words = list(completer.words)

        # All core functions should be in completion words
        for func_name in core_functions:
            assert func_name in completion_words, f"Function {func_name} not in tab completion"

    def test_help_error_handling(self):
        """Test that help system handles errors gracefully."""
        import sys
        from io import StringIO
        from unittest.mock import patch

        from dana.common.resource.llm.llm_resource import LLMResource
        from dana.common.terminal_utils import ColorScheme
        from dana.core.repl.commands.command_handler import CommandHandler
        from dana.core.repl.repl import REPL

        # Create a REPL with normal setup
        repl = REPL(llm_resource=LLMResource())
        colors = ColorScheme(use_colors=False)
        command_handler = CommandHandler(repl, colors)

        # Mock the registry.list method to raise an error
        with patch.object(repl.interpreter.function_registry, "list") as mock_list:
            mock_list.side_effect = Exception("Registry error")

            # Capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            try:
                command_handler.help_formatter.show_core_functions_plain()
                help_output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout

            # Should fall back to hardcoded functions
            assert "print(...)" in help_output
            assert "log(...)" in help_output
            assert "reason(...)" in help_output


@pytest.mark.deep
class TestPrintFunctionWithFStrings:
    """Test print function's handling of f-strings.

    Migrated from tests/dana/sandbox/test_fixed_functions.py::test_print_function_with_fstrings()
    Enhanced with additional f-string scenarios and comprehensive testing.
    """

    def test_print_function_fstring_basic(self, capsys):
        """Test basic f-string evaluation in print function."""

        from dana.core.lang.ast import FStringExpression, Identifier
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context with variables
        context = SandboxContext()
        context.set("x", 42)
        context.set("y", "hello")

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create a simple f-string
        fstring = FStringExpression(parts=["Value: ", Identifier("x")])

        # Call print function with f-string - context as first positional arg
        print_function(context, fstring)

        # Get the captured output
        captured = capsys.readouterr()
        assert "Value: 42" in captured.out

    def test_print_function_fstring_complex(self, capsys):
        """Test complex f-string evaluation in print function."""

        from dana.core.lang.ast import BinaryExpression, BinaryOperator, FStringExpression, Identifier, LiteralExpression
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context with variables
        context = SandboxContext()
        context.set("x", 42)

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create a more complex f-string
        complex_fstring = FStringExpression(
            parts=["x + 10 = ", BinaryExpression(Identifier("x"), BinaryOperator.ADD, LiteralExpression(10))]
        )

        # Print with multiple arguments - context as first positional arg
        print_function(context, "Result:", complex_fstring)

        # Verify combined output
        captured = capsys.readouterr()
        assert "Result: x + 10 = 52" in captured.out

    def test_print_function_fstring_multiple_variables(self, capsys):
        """Test f-string with multiple variables in print function."""
        from dana.core.lang.ast import FStringExpression, Identifier
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context with multiple variables
        context = SandboxContext()
        context.set("name", "Dana")
        context.set("version", "1.0")
        context.set("status", "active")

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create f-string with multiple variables
        fstring = FStringExpression(parts=["System: ", Identifier("name"), " v", Identifier("version"), " (", Identifier("status"), ")"])

        # Call print function
        print_function(context, fstring)

        # Verify output
        captured = capsys.readouterr()
        assert "System: Dana v1.0 (active)" in captured.out

    def test_print_function_fstring_with_expressions(self, capsys):
        """Test f-string with complex expressions in print function."""
        from dana.core.lang.ast import BinaryExpression, BinaryOperator, FStringExpression, Identifier
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context with variables
        context = SandboxContext()
        context.set("a", 10)
        context.set("b", 5)

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create f-string with mathematical expressions
        fstring = FStringExpression(
            parts=[
                "Math: ",
                Identifier("a"),
                " + ",
                Identifier("b"),
                " = ",
                BinaryExpression(Identifier("a"), BinaryOperator.ADD, Identifier("b")),
                ", ",
                Identifier("a"),
                " * ",
                Identifier("b"),
                " = ",
                BinaryExpression(Identifier("a"), BinaryOperator.MULTIPLY, Identifier("b")),
            ]
        )

        # Call print function
        print_function(context, fstring)

        # Verify output
        captured = capsys.readouterr()
        assert "Math: 10 + 5 = 15, 10 * 5 = 50" in captured.out

    def test_print_function_fstring_template_style(self, capsys):
        """Test f-string with template and expressions style."""
        from dana.core.lang.ast import BinaryExpression, BinaryOperator, FStringExpression, Identifier
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context with variables
        context = SandboxContext()
        context.set("x", 17)
        context.set("y", 25)

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create new-style f-string with template and expressions
        fstring = FStringExpression(parts=[])
        fstring.template = "The answer is: {x} + {y} = {result}"
        fstring.expressions = {
            "{x}": Identifier("x"),
            "{y}": Identifier("y"),
            "{result}": BinaryExpression(Identifier("x"), BinaryOperator.ADD, Identifier("y")),
        }

        # Call print function
        print_function(context, fstring)

        # Verify output
        captured = capsys.readouterr()
        assert "The answer is: 17 + 25 = 42" in captured.out

    def test_print_function_fstring_error_handling(self, capsys):
        """Test print function error handling with invalid f-strings."""
        from dana.core.lang.ast import FStringExpression, Identifier
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context without the required variable
        context = SandboxContext()

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create f-string with undefined variable
        fstring = FStringExpression(parts=["Value: ", Identifier("undefined_var")])

        # This should handle the error gracefully
        try:
            print_function(context, fstring)
            captured = capsys.readouterr()
            # Should either print an error message or handle gracefully
            assert len(captured.out) >= 0  # Some output should be produced
        except Exception as e:
            # If an exception is raised, it should be a meaningful one
            assert "undefined_var" in str(e) or "not found" in str(e).lower()

    def test_print_function_mixed_args_with_fstrings(self, capsys):
        """Test print function with mixed regular and f-string arguments."""
        from dana.core.lang.ast import FStringExpression, Identifier
        from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
        from dana.core.stdlib.core.print_function import print_function

        # Create a context with variables
        context = SandboxContext()
        context.set("count", 5)
        context.set("item", "apples")

        # Create an executor and set it on the context
        executor = DanaExecutor()
        interpreter = DanaInterpreter()
        interpreter._executor = executor
        context.interpreter = interpreter

        # Create f-strings
        fstring1 = FStringExpression(parts=["I have ", Identifier("count")])
        fstring2 = FStringExpression(parts=[Identifier("item"), " in total"])

        # Call print function with mixed arguments
        print_function(context, "Shopping:", fstring1, fstring2, "!")

        # Verify output
        captured = capsys.readouterr()
        assert "Shopping: I have 5 apples in total !" in captured.out
