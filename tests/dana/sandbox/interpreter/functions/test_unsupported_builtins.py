"""
Tests for unsupported Pythonic built-in functions.

These tests verify that unsupported functions are properly blocked with
appropriate error messages and security rationales.
"""

import pytest

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import (
    PythonicFunctionFactory,
    UnsupportedReason,
    register_pythonic_builtins,
)
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestUnsupportedFunctions:
    """Test class for unsupported function handling."""

    def test_unsupported_function_detection(self):
        """Test that unsupported functions are properly detected."""
        factory = PythonicFunctionFactory()

        # Test known unsupported functions
        assert factory.is_unsupported("eval")
        assert factory.is_unsupported("exec")
        assert factory.is_unsupported("open")
        assert factory.is_unsupported("print")
        assert factory.is_unsupported("globals")
        assert factory.is_unsupported("locals")

        # Test that supported functions are not marked as unsupported
        assert not factory.is_unsupported("len")
        assert not factory.is_unsupported("sum")
        assert not factory.is_unsupported("max")

    def test_eval_function_blocked(self):
        """Test that eval() is properly blocked."""
        factory = PythonicFunctionFactory()

        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("eval")

        error_msg = str(exc_info.value)
        assert "eval" in error_msg
        assert "not supported" in error_msg
        assert "arbitrary code execution" in error_msg.lower()
        assert "Alternative:" in error_msg

    def test_exec_function_blocked(self):
        """Test that exec() is properly blocked."""
        factory = PythonicFunctionFactory()

        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("exec")

        error_msg = str(exc_info.value)
        assert "exec" in error_msg
        assert "not supported" in error_msg
        assert "arbitrary code execution" in error_msg.lower()

    def test_open_function_blocked(self):
        """Test that open() is properly blocked."""
        factory = PythonicFunctionFactory()

        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("open")

        error_msg = str(exc_info.value)
        assert "open" in error_msg
        assert "not supported" in error_msg
        assert "file" in error_msg.lower()

    def test_print_function_blocked(self):
        """Test that print() is properly blocked."""
        factory = PythonicFunctionFactory()

        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("print")

        error_msg = str(exc_info.value)
        assert "print" in error_msg
        assert "not supported" in error_msg
        assert "output" in error_msg.lower()

    def test_globals_locals_blocked(self):
        """Test that globals() and locals() are properly blocked."""
        factory = PythonicFunctionFactory()

        # Test globals()
        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("globals")

        error_msg = str(exc_info.value)
        assert "globals" in error_msg
        assert "security" in error_msg.lower()

        # Test locals()
        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("locals")

        error_msg = str(exc_info.value)
        assert "locals" in error_msg
        assert "security" in error_msg.lower()

    def test_import_function_blocked(self):
        """Test that __import__ is properly blocked."""
        factory = PythonicFunctionFactory()

        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("__import__")

        error_msg = str(exc_info.value)
        assert "__import__" in error_msg
        assert "import" in error_msg.lower()

    def test_attribute_manipulation_blocked(self):
        """Test that attribute manipulation functions are blocked."""
        factory = PythonicFunctionFactory()

        blocked_functions = ["getattr", "setattr", "delattr", "hasattr"]

        for func_name in blocked_functions:
            with pytest.raises(SandboxError) as exc_info:
                factory.create_function(func_name)

            error_msg = str(exc_info.value)
            assert func_name in error_msg
            assert "not supported" in error_msg

    def test_memory_access_blocked(self):
        """Test that memory access functions are blocked."""
        factory = PythonicFunctionFactory()

        blocked_functions = ["id", "memoryview"]

        for func_name in blocked_functions:
            with pytest.raises(SandboxError) as exc_info:
                factory.create_function(func_name)

            error_msg = str(exc_info.value)
            assert func_name in error_msg
            assert "memory" in error_msg.lower()

    def test_type_introspection_blocked(self):
        """Test that type introspection functions are handled correctly."""
        factory = PythonicFunctionFactory()
        context = SandboxContext()

        # type() is now supported
        type_func = factory.create_function("type")
        assert type_func(context, 42) == "int"
        assert type_func(context, "hello") == "str"
        assert type_func(context, [1, 2, 3]) == "list"
        assert type_func(context, {"a": 1}) == "dict"
        assert type_func(context, 3.14) == "float"
        assert type_func(context, True) == "bool"

        # The others are still blocked
        blocked_functions = ["isinstance", "issubclass", "callable"]
        for func_name in blocked_functions:
            with pytest.raises(SandboxError) as exc_info:
                factory.create_function(func_name)
            error_msg = str(exc_info.value)
            assert func_name in error_msg
            assert "not supported" in error_msg

    def test_unsupported_info_retrieval(self):
        """Test retrieving information about unsupported functions."""
        factory = PythonicFunctionFactory()

        # Test getting info for eval
        eval_info = factory.get_unsupported_info("eval")
        assert eval_info["reason"] == UnsupportedReason.ARBITRARY_CODE_EXECUTION
        assert "code evaluation" in eval_info["message"]
        assert "alternative" in eval_info

        # Test getting info for open
        open_info = factory.get_unsupported_info("open")
        assert open_info["reason"] == UnsupportedReason.FILE_SYSTEM_ACCESS
        assert "file" in open_info["message"].lower()

    def test_functions_by_reason(self):
        """Test getting functions grouped by unsupported reason."""
        factory = PythonicFunctionFactory()

        # Test security risk functions
        security_risks = factory.get_functions_by_reason(UnsupportedReason.SECURITY_RISK)
        assert "globals" in security_risks
        assert "locals" in security_risks
        assert "getattr" in security_risks

        # Test arbitrary code execution functions
        code_exec = factory.get_functions_by_reason(UnsupportedReason.ARBITRARY_CODE_EXECUTION)
        assert "eval" in code_exec
        assert "exec" in code_exec
        assert "__import__" in code_exec

        # Test file system access functions
        file_access = factory.get_functions_by_reason(UnsupportedReason.FILE_SYSTEM_ACCESS)
        assert "open" in file_access

    def test_security_report(self):
        """Test the security report functionality."""
        factory = PythonicFunctionFactory()
        report = factory.get_security_report()

        # Check report structure
        assert "supported_functions" in report
        assert "unsupported_functions" in report
        assert "unsupported_by_reason" in report
        assert "security_critical" in report

        # Check counts
        assert report["supported_functions"] > 0
        assert report["unsupported_functions"] > 0

        # Check that security-critical functions are identified
        assert len(report["security_critical"]) > 0
        assert "eval" in report["security_critical"]
        assert "exec" in report["security_critical"]

    def test_unknown_builtin_handling(self):
        """Test handling of unknown Python built-in functions."""
        factory = PythonicFunctionFactory()

        # Test with a known Python built-in that's not in our lists
        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("zip")  # zip is a real Python built-in

        error_msg = str(exc_info.value)
        assert "zip" in error_msg
        assert "not available" in error_msg
        assert "Supported built-ins:" in error_msg

        # Test with a completely unknown function
        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("totally_fake_function")

        error_msg = str(exc_info.value)
        assert "totally_fake_function" in error_msg
        assert "not a recognized built-in" in error_msg


class TestUnsupportedFunctionRegistry:
    """Test unsupported function handling in the registry."""

    def test_unsupported_functions_registered(self):
        """Test that unsupported functions are registered with error handlers."""
        registry = FunctionRegistry()
        register_pythonic_builtins(registry)

        # Test that unsupported functions are "registered" (with error handlers)
        assert registry.has("eval")
        assert registry.has("exec")
        assert registry.has("open")

    def test_calling_unsupported_through_registry(self):
        """Test calling unsupported functions through the registry."""
        registry = FunctionRegistry()
        register_pythonic_builtins(registry)
        context = SandboxContext()

        # Test calling eval through registry
        with pytest.raises(SandboxError) as exc_info:
            registry.call("eval", context, args=["1 + 1"])

        error_msg = str(exc_info.value)
        assert "eval" in error_msg
        assert "not supported" in error_msg

        # Test calling open through registry
        with pytest.raises(SandboxError) as exc_info:
            registry.call("open", context, args=["test.txt"])

        error_msg = str(exc_info.value)
        assert "open" in error_msg
        assert "not supported" in error_msg

    def test_unsupported_function_precedence(self):
        """Test that built-in handlers override user-defined functions."""
        registry = FunctionRegistry()

        # Register a custom eval function first
        def safe_eval(context, expr):
            return f"Safe evaluation of: {expr}"

        from opendxa.dana.sandbox.interpreter.functions.python_function import PythonFunction

        registry.register("eval", PythonFunction(safe_eval, trusted_for_context=True), func_type="python", overwrite=True)

        # Now register built-ins (should overwrite the custom eval with error handler)
        register_pythonic_builtins(registry)

        # The built-in error handler should now be active, not the custom function
        context = SandboxContext()
        with pytest.raises(SandboxError) as exc_info:
            registry.call("eval", context, args=["test"])

        error_msg = str(exc_info.value)
        assert "eval" in error_msg
        assert "not supported" in error_msg


@pytest.mark.deep
class TestUnsupportedFunctionIntegration:
    """Test unsupported function handling with the Dana interpreter."""

    def test_interpreter_blocks_unsupported_functions(self):
        """Test that the interpreter properly blocks unsupported functions."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test that unsupported functions are registered
        assert interpreter.function_registry.has("eval")
        assert interpreter.function_registry.has("open")

        # Test calling through interpreter should raise errors
        with pytest.raises(SandboxError):
            interpreter.function_registry.call("eval", context, args=["1 + 1"])

        with pytest.raises(SandboxError):
            interpreter.function_registry.call("open", context, args=["test.txt"])

    def test_interpreter_error_messages(self):
        """Test that interpreter provides helpful error messages."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test eval error message
        with pytest.raises(SandboxError) as exc_info:
            interpreter.function_registry.call("eval", context, args=["1 + 1"])

        error_msg = str(exc_info.value)
        assert "eval" in error_msg
        assert "security" in error_msg.lower() or "code execution" in error_msg.lower()
        assert "Alternative:" in error_msg

    def test_supported_vs_unsupported_coexistence(self):
        """Test that supported and unsupported functions coexist properly."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Supported function should work
        result = interpreter.function_registry.call("len", context, args=[[1, 2, 3]])
        assert result == 3

        # Unsupported function should fail
        with pytest.raises(SandboxError):
            interpreter.function_registry.call("eval", context, args=["1 + 1"])


@pytest.mark.deep
class TestUnsupportedFunctionEdgeCases:
    """Test edge cases for unsupported function handling."""

    def test_case_sensitivity(self):
        """Test that function names are case-sensitive."""
        factory = PythonicFunctionFactory()

        # eval is unsupported
        assert factory.is_unsupported("eval")

        # EVAL should be treated as unknown, not unsupported
        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("EVAL")

        error_msg = str(exc_info.value)
        assert "EVAL" in error_msg
        assert "not a recognized built-in" in error_msg

    def test_empty_function_name(self):
        """Test handling of empty function names."""
        factory = PythonicFunctionFactory()

        with pytest.raises(SandboxError) as exc_info:
            factory.create_function("")

        error_msg = str(exc_info.value)
        assert "not a recognized built-in" in error_msg

    def test_none_function_name(self):
        """Test handling of None as function name."""
        factory = PythonicFunctionFactory()

        with pytest.raises((SandboxError, TypeError, AttributeError)):
            factory.create_function(None)  # type: ignore

    def test_numeric_function_name(self):
        """Test handling of numeric function names."""
        factory = PythonicFunctionFactory()

        with pytest.raises((SandboxError, TypeError)):
            factory.create_function(123)  # type: ignore

    def test_unsupported_info_for_unknown_function(self):
        """Test getting unsupported info for unknown functions."""
        factory = PythonicFunctionFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.get_unsupported_info("unknown_function")

        assert "not in the unsupported list" in str(exc_info.value)

    def test_comprehensive_unsupported_coverage(self):
        """Test that all major categories of unsupported functions are covered."""
        factory = PythonicFunctionFactory()
        unsupported = factory.get_unsupported_functions()

        # Check that we have functions from each major security category
        categories_found = set()

        for func_name in unsupported:
            info = factory.get_unsupported_info(func_name)
            categories_found.add(info["reason"])

        # Verify we have coverage of major security concerns
        expected_categories = {
            UnsupportedReason.SECURITY_RISK,
            UnsupportedReason.ARBITRARY_CODE_EXECUTION,
            UnsupportedReason.FILE_SYSTEM_ACCESS,
            UnsupportedReason.MEMORY_SAFETY,
        }

        for category in expected_categories:
            assert category in categories_found, f"Missing coverage for {category}"
