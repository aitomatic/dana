"""Unit tests for PythonSandbox."""

import pytest

from dana.core.agent.components.python_sandbox import PythonSandbox


class TestPythonSandbox:
    """Tests for PythonSandbox class."""

    def test_basic_execution(self):
        """Test that print works."""
        sandbox = PythonSandbox()
        output = sandbox.execute("print('hello world')", context="")
        assert "hello world" in output

    def test_context_variable(self):
        """Test that context is accessible."""
        sandbox = PythonSandbox()
        output = sandbox.execute("print(context)", context="test content")
        assert "test content" in output

    def test_context_slicing(self):
        """Test that we can slice context."""
        sandbox = PythonSandbox()
        output = sandbox.execute("print(context[:5])", context="hello world")
        assert "hello" in output
        assert "world" not in output

    def test_safe_modules_available(self):
        """Test that re, json, math work."""
        sandbox = PythonSandbox()

        # Test re
        output = sandbox.execute("print(re.findall(r'\\d+', context))", context="abc 123 def 456")
        assert "123" in output
        assert "456" in output

        # Test json
        output = sandbox.execute("print(json.dumps({'a': 1}))", context="")
        assert '{"a": 1}' in output

        # Test math
        output = sandbox.execute("print(math.sqrt(16))", context="")
        assert "4.0" in output

    def test_namespace_persistence(self):
        """Test that variables persist across calls."""
        sandbox = PythonSandbox()

        # First execution - set a variable
        sandbox.execute("x = 42", context="")

        # Second execution - access the variable
        output = sandbox.execute("print(x)", context="")
        assert "42" in output

    def test_llm_query_function(self):
        """Test that llm_query works when provided."""

        def mock_llm_query(prompt: str, text: str) -> str:
            return f"Mock response for: {prompt}"

        sandbox = PythonSandbox(llm_query_fn=mock_llm_query)
        output = sandbox.execute("result = llm_query('summarize', 'some text')\nprint(result)", context="")
        assert "Mock response for: summarize" in output

    def test_output_truncation(self):
        """Test that long output is truncated to 10KB."""
        sandbox = PythonSandbox()
        # Generate output larger than 10KB
        output = sandbox.execute("print('x' * 20000)", context="")
        assert len(output) <= 10 * 1024 + 100  # Allow some overhead for truncation message
        assert "truncated" in output.lower()

    def test_error_handling(self):
        """Test that errors are captured in output."""
        sandbox = PythonSandbox()
        output = sandbox.execute("raise ValueError('test error')", context="")
        assert "Error" in output
        assert "ValueError" in output
        assert "test error" in output

    def test_dangerous_builtins_blocked(self):
        """Test that eval, exec, open are blocked."""
        sandbox = PythonSandbox()

        # Test eval blocked
        output = sandbox.execute("eval('1+1')", context="")
        assert "Error" in output

        # Test exec blocked
        output = sandbox.execute("exec('print(1)')", context="")
        assert "Error" in output

        # Test open blocked
        output = sandbox.execute("open('/etc/passwd')", context="")
        assert "Error" in output

        # Test __import__ blocked
        output = sandbox.execute("__import__('os')", context="")
        assert "Error" in output

    def test_reset(self):
        """Test that reset clears namespace."""
        sandbox = PythonSandbox()

        # Set a variable
        sandbox.execute("x = 42", context="")

        # Reset
        sandbox.reset()

        # Variable should no longer exist
        output = sandbox.execute("print(x)", context="")
        assert "Error" in output
        assert "NameError" in output


class TestPythonSandboxEdgeCases:
    """Edge case tests for PythonSandbox."""

    def test_empty_code(self):
        """Test executing empty code."""
        sandbox = PythonSandbox()
        output = sandbox.execute("", context="test")
        assert output == ""  # No output for empty code

    def test_multiline_code(self):
        """Test executing multiline code."""
        sandbox = PythonSandbox()
        code = """
for i in range(3):
    print(i)
"""
        output = sandbox.execute(code, context="")
        assert "0" in output
        assert "1" in output
        assert "2" in output

    def test_collections_module(self):
        """Test collections module is available."""
        sandbox = PythonSandbox()
        # Modules are pre-injected, so use them directly without import
        output = sandbox.execute("print(collections.Counter('aabbc'))", context="")
        assert "Counter" in output
        assert "'a': 2" in output

    def test_itertools_module(self):
        """Test itertools module is available."""
        sandbox = PythonSandbox()
        # Modules are pre-injected, so use them directly without import
        output = sandbox.execute("print(list(itertools.chain([1,2], [3,4])))", context="")
        assert "[1, 2, 3, 4]" in output

    def test_functools_module(self):
        """Test functools module is available."""
        sandbox = PythonSandbox()
        # Modules are pre-injected, so use them directly without import
        code = """
result = functools.reduce(lambda x, y: x + y, [1, 2, 3, 4])
print(result)
"""
        output = sandbox.execute(code, context="")
        assert "10" in output

    def test_context_not_persisted(self):
        """Test that context variable doesn't persist between calls."""
        sandbox = PythonSandbox()

        # First call with context
        sandbox.execute("x = len(context)", context="hello")

        # Second call with different context - x should still be 5 from first call
        output = sandbox.execute("print(x, len(context))", context="hi")
        assert "5 2" in output  # x=5 persisted, context=2 is new
