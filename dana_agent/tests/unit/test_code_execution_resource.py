"""Unit tests for CodeExecutionResource."""

import pytest

from dana.common.resource import CodeExecutionResource


class TestCodeExecutionResource:
    """Tests for CodeExecutionResource class."""

    def test_initialization(self):
        """Test CodeExecutionResource initialization."""
        resource = CodeExecutionResource(auto_register=False)

        assert resource.resource_type == "code-execution"
        assert hasattr(resource, "execute")
        assert hasattr(resource, "reset")
        assert resource.execute_count == 0

    def test_execute_simple_expression(self):
        """Test executing simple expression and returns stdout."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("print(2 + 2)")

        assert "4" in result
        assert resource.execute_count == 1

    def test_execute_multiline_code(self):
        """Test executing multi-line code and preserves variables across calls."""
        resource = CodeExecutionResource(auto_register=False)

        # First execution - set variables
        result1 = resource.execute("""
x = 10
y = 20
print(x + y)
""")
        assert "30" in result1

        # Second execution - use variables from first
        result2 = resource.execute("print(x * y)")
        assert "200" in result2

    def test_blocks_open(self):
        """Test that open() is blocked and returns clear error."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("open('/etc/passwd')")

        assert "Error" in result
        assert "PermissionError" in result
        assert "open" in result

    def test_blocks_import(self):
        """Test that __import__ is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("__import__('os')")

        assert "Error" in result
        assert "PermissionError" in result
        assert "__import__" in result

    def test_blocks_non_whitelisted_module_import(self):
        """Test that non-whitelisted module import is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        # Try to import a module not in whitelist
        result = resource.execute("import os")

        # Should either block at validation or during execution
        assert "Error" in result or "not allowed" in result.lower()

    def test_allows_whitelisted_module_import(self):
        """Test that whitelisted module import works (e.g., statistics)."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("""
import statistics
print(statistics.mean([1, 2, 3, 4, 5]))
""")

        assert "3" in result or "3.0" in result
        assert "Error" not in result

    def test_allows_whitelisted_modules_directly(self):
        """Test that whitelisted modules are available directly."""
        resource = CodeExecutionResource(auto_register=False)

        # math, json, re are pre-injected
        result = resource.execute("print(math.sqrt(16))")
        assert "4.0" in result

        result = resource.execute("print(json.dumps({'a': 1}))")
        assert '{"a": 1}' in result

    def test_timeout_on_infinite_loop(self):
        """Test that timeout is respected on infinite loop."""
        resource = CodeExecutionResource(timeout_seconds=0.1, auto_register=False)

        result = resource.execute("""
while True:
    pass
""")

        # Should timeout (may vary by platform)
        assert "Error" in result or "timeout" in result.lower() or "TimeoutError" in result

    def test_output_truncation(self):
        """Test that output is truncated over max size."""
        resource = CodeExecutionResource(max_output_size=100, auto_register=False)

        # Generate output larger than max
        result = resource.execute("print('x' * 200)")

        # Should be truncated
        assert len(result) <= 150  # Allow some overhead for truncation message
        assert "truncated" in result.lower() or len(result) < 200

    def test_reset_clears_namespace(self):
        """Test that reset() clears namespace and confirms reset."""
        resource = CodeExecutionResource(auto_register=False)

        # Set a variable
        resource.execute("x = 42")

        # Reset
        result = resource.reset()
        assert "reset" in result.lower()
        assert resource.execute_count == 0

        # Variable should no longer exist
        result2 = resource.execute("print(x)")
        assert "Error" in result2
        assert "NameError" in result2

    def test_syntax_error_handling(self):
        """Test that syntax errors are caught and reported."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("print(")  # Missing closing paren

        assert "Error" in result
        assert "SyntaxError" in result

    def test_runtime_error_handling(self):
        """Test that runtime errors are caught and reported."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("1 / 0")

        assert "Error" in result
        assert "ZeroDivisionError" in result

    def test_allowed_modules_parameter(self):
        """Test that allowed_modules parameter extends whitelist."""
        resource = CodeExecutionResource(
            allowed_modules=["decimal"], auto_register=False
        )

        result = resource.execute("""
import decimal
print(decimal.Decimal('1.5'))
""")

        assert "1.5" in result
        assert "Error" not in result

    def test_empty_code(self):
        """Test executing empty code."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("")

        # Should handle gracefully
        assert isinstance(result, str)

    def test_blocks_eval(self):
        """Test that eval is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("eval('1+1')")

        assert "Error" in result
        assert "PermissionError" in result
        assert "eval" in result

    def test_blocks_exec(self):
        """Test that exec is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("exec('print(1)')")

        assert "Error" in result
        assert "PermissionError" in result
        assert "exec" in result

    def test_blocks_compile(self):
        """Test that compile is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("compile('1+1', '<string>', 'eval')")

        assert "Error" in result
        assert "PermissionError" in result
        assert "compile" in result

    def test_blocks_input(self):
        """Test that input is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("input('test')")

        assert "Error" in result
        assert "PermissionError" in result
        assert "input" in result

    def test_blocks_breakpoint(self):
        """Test that breakpoint is blocked."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("breakpoint()")

        assert "Error" in result
        assert "PermissionError" in result
        assert "breakpoint" in result

    def test_datetime_module_available(self):
        """Test that datetime module is available."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("""
import datetime
print(datetime.datetime.now().year)
""")

        # Should print current year (or at least not error)
        assert "Error" not in result or "20" in result  # Year should be 20xx

    def test_random_module_available(self):
        """Test that random module is available."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("""
import random
x = random.randint(1, 10)
print(x >= 1 and x <= 10)
""")

        assert "True" in result
        assert "Error" not in result

    def test_string_module_available(self):
        """Test that string module is available."""
        resource = CodeExecutionResource(auto_register=False)

        result = resource.execute("""
import string
print(string.ascii_lowercase[:5])
""")

        assert "abcde" in result
        assert "Error" not in result
