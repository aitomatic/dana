"""
Tests for POET function registry and decorator functionality.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

import pytest

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


@pytest.mark.poet
class TestPOETRegistry:
    """Test POET function registry and decorator functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.sandbox = DanaSandbox()
        self.tmp_dir = Path("tmp")
        self.tmp_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up sandbox
        if hasattr(self, "sandbox"):
            self.sandbox._cleanup()

        # Clean up temporary files
        for file in self.tmp_dir.glob("test_poet_*.na"):
            file.unlink()

    def test_poet_function_registration(self):
        """Test that POET functions are properly registered in the function registry"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_registration.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def test_func(x: int) -> int:
    return x * 2

# Test the function
result = test_func(5)
assert result == 10
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 10

    def test_poet_function_execution(self):
        """Test execution of registered POET functions"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_execution.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def test_func(x: int) -> int:
    return x * 2

# Test the function
result = test_func(5)
assert result == 10
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 10

    def test_poet_function_with_context(self):
        """Test POET functions with sandbox context"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_context.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def context_func(context: SandboxContext, x: int) -> int:
    return x * 2

# Test the function
result = context_func(5)
assert result == 10
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 10

    def test_poet_function_namespace(self):
        """Test POET functions with different namespaces"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_namespace.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def test_func(x: int) -> int:
    return x * 2

# Test the function in different namespace
result = test_func(5)
assert result == 10
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 10

    def test_poet_function_overwrite(self):
        """Test overwriting registered POET functions"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_overwrite.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def test_func(x: int) -> int:
    return x * 2

# Test initial function
result = test_func(5)
assert result == 10

# Redefine the function
# @poet(domain="test_domain")
def test_func(x: int) -> int:
    return x * 3

# Test new function
result = test_func(5)
assert result == 15
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 15

    def test_poet_function_metadata(self):
        """Test POET function metadata preservation"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_metadata.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def test_func(x: int) -> int:
    \"\"\"Test function docstring.\"\"\"
    return x * 2

# Test the function
result = test_func(5)
assert result == 10
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 10

    def test_poet_function_error_handling(self):
        """Test error handling in registered POET functions"""
        # Create a test .na file
        test_file = Path("tmp/test_poet_error.na")
        test_file.write_text(
            """
# @poet(domain="test_domain")
def error_func(x: int) -> int:
    if x < 0:
        raise ValueError("Negative input not allowed")
    return x * 2

# Test normal execution
result = error_func(5)
assert result == 10

# Test error case
try:
    error_func(-5)
    assert false, "Should have raised ValueError"
except ValueError:
    pass  # Expected error
"""
        )

        # Run the file
        result = self.sandbox.run(test_file)
        assert result.success
        # Check the computed result in the final context
        assert result.final_context is not None
        assert result.final_context.get("local:result") == 10
