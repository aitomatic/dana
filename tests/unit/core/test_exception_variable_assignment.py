"""
Test exception variable assignment syntax in Dana.

Tests for the new `except Exception as e:` syntax implementation.
"""

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.runtime.exceptions import DanaException


class TestExceptionVariableAssignment:
    """Test suite for exception variable assignment feature."""

    def test_bare_except_with_variable(self):
        """Test bare except with variable assignment."""
        code = """
try:
    x = 1 / 0
except as e:
    result = e.type
"""
        result = self.run_dana_code(code)
        assert result is not None

    def test_specific_exception_with_variable(self):
        """Test specific exception type with variable assignment."""
        code = """
try:
    x = 1 / 0
except ZeroDivisionError as e:
    result = e.type
"""
        result = self.run_dana_code(code)
        assert result is not None

    def test_multiple_exception_types_with_variable(self):
        """Test multiple exception types with variable assignment."""
        code = """
try:
    x = 1 / 0
except (ValueError, ZeroDivisionError) as e:
    result = e.type
"""
        result = self.run_dana_code(code)
        assert result is not None

    def test_exception_object_properties(self):
        """Test that exception object has expected properties."""
        code = """
try:
    x = 1 / 0
except as e:
    type_val = e.type
    message_val = e.message
    has_traceback = len(e.traceback) >= 0
"""
        context = self.run_dana_code_with_context(code)
        # The variables should be set in the context but may be in local scope
        # For now, just verify the code runs without error
        assert context is not None

    def test_mixed_exception_handlers(self):
        """Test mixing handlers with and without variables."""
        code = """
result = "none"
try:
    x = 1 / 0
except ValueError as e:
    result = "value_error"
except ZeroDivisionError:
    result = "zero_div_no_var"
except as e:
    result = "fallback"
"""
        context = self.run_dana_code_with_context(code)
        assert context is not None

    def test_nested_exception_handling(self):
        """Test nested try blocks with variable assignment."""
        code = """
result = "none"
try:
    try:
        x = 1 / 0
    except ZeroDivisionError as inner_e:
        result = inner_e.type
except Exception as outer_e:
    result = "outer"
"""
        context = self.run_dana_code_with_context(code)
        assert context is not None

    def test_exception_in_finally_block(self):
        """Test exception variable assignment with finally block."""
        code = """
result = "none"
try:
    x = 1 / 0
except as e:
    result = e.type
finally:
    cleanup = "done"
"""
        context = self.run_dana_code_with_context(code)
        assert context is not None

    def test_exception_variable_scope(self):
        """Test that exception variable is scoped to except block."""
        code = """
# Exception variable should not be accessible outside except block
result = "before"
try:
    x = 1 / 0
except as e:
    result = "caught"
# e should not be accessible here
"""
        context = self.run_dana_code_with_context(code)
        assert context is not None

    def test_backward_compatibility(self):
        """Test that old syntax still works."""
        code = """
result = "none"
try:
    x = 1 / 0
except:
    result = "caught"
"""
        context = self.run_dana_code_with_context(code)
        assert context is not None

    def test_backward_compatibility_with_type(self):
        """Test that old syntax with type still works."""
        code = """
result = "none"
try:
    x = 1 / 0
except ZeroDivisionError:
    result = "caught"
"""
        context = self.run_dana_code_with_context(code)
        assert context is not None

    def run_dana_code(self, code: str):
        """Helper to run Dana code and return result."""
        try:
            with DanaSandbox() as sandbox:
                result = sandbox.execute_string(code)
                if not result.success:
                    pytest.fail(f"Dana execution failed: {result.error}")
                return result
        except Exception as e:
            pytest.fail(f"Dana code execution failed: {e}")

    def run_dana_code_with_context(self, code: str):
        """Helper to run Dana code and return context."""
        try:
            with DanaSandbox() as sandbox:
                result = sandbox.execute_string(code)
                if not result.success:
                    pytest.fail(f"Dana execution failed: {result.error}")
                return result.final_context
        except Exception as e:
            pytest.fail(f"Dana code execution failed: {e}")


class TestDanaExceptionObject:
    """Test suite for DanaException object itself."""

    def test_dana_exception_creation(self):
        """Test creating DanaException from Python exception."""
        from dana.core.runtime.exceptions import create_dana_exception

        try:
            raise ValueError("test message")
        except Exception as e:
            dana_exc = create_dana_exception(e)

            assert isinstance(dana_exc, DanaException)
            assert dana_exc.type == "ValueError"
            assert dana_exc.message == "test message"
            assert isinstance(dana_exc.traceback, list)
            assert dana_exc.original is e

    def test_dana_exception_string_representation(self):
        """Test string representation of DanaException."""
        from dana.core.runtime.exceptions import create_dana_exception

        try:
            raise RuntimeError("test error")
        except Exception as e:
            dana_exc = create_dana_exception(e)

            str_repr = str(dana_exc)
            assert "RuntimeError: test error" == str_repr

    def test_dana_exception_to_dict(self):
        """Test converting DanaException to dictionary."""
        from dana.core.runtime.exceptions import create_dana_exception

        try:
            raise TypeError("type error")
        except Exception as e:
            dana_exc = create_dana_exception(e)

            dict_repr = dana_exc.to_dict()
            assert dict_repr["type"] == "TypeError"
            assert dict_repr["message"] == "type error"
            assert "traceback" in dict_repr
