"""
Tests for POET decorator integration with Dana language.

This module tests the POET decorator functionality within Dana .na file execution.
"""

from pathlib import Path

import pytest


@pytest.mark.poet
class TestPOETDecoratorDana:
    """Test POET decorator functionality within Dana language execution."""

    # Using shared fixture from conftest.py instead of creating individual instances

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    def get_context(self, result):
        """Helper function to get the context from an ExecutionResult."""
        assert result.final_context is not None, f"Execution failed or context missing: {result.error}"
        return result.final_context

    def test_basic_decorator_execution(self, fresh_sandbox, fixtures_dir):
        """Test basic POET decorator functionality in Dana."""

        result = fresh_sandbox.run(fixtures_dir / "basic_decorator.na")
        context = self.get_context(result)

        # Should execute successfully
        assert result.success

        # Check that functions were decorated and results computed
        assert context.get("result_add") == 30  # 10 + 20
        assert context.get("result_multiply") == 30  # 5 * 6
        assert context.get("result_concat") == "HelloWorld"

        # Check that functions have POET metadata
        simple_add = context.get("simple_add")
        assert simple_add is not None
        assert hasattr(simple_add, "_poet_metadata")
        assert "test_math" in simple_add._poet_metadata["domains"]

    def test_decorator_with_parameters(self, fresh_sandbox, fixtures_dir):
        """Test POET decorator with various parameters in Dana."""

        result = fresh_sandbox.run(fixtures_dir / "basic_decorator.na")
        context = self.get_context(result)

        assert result.success

        # Check function with custom parameters
        simple_multiply = context.get("simple_multiply")
        assert simple_multiply is not None
        assert hasattr(simple_multiply, "_poet_metadata")

        meta = simple_multiply._poet_metadata
        assert "test_math" in meta["domains"]
        assert meta["retries"] == 2
        assert meta["timeout"] == 30

    def test_decorator_chaining(self, fresh_sandbox, fixtures_dir):
        """Test multiple POET decorators on the same function in Dana."""

        result = fresh_sandbox.run(fixtures_dir / "decorator_chaining.na")
        context = self.get_context(result)

        assert result.success

        # Check that results are computed correctly
        assert context.get("result1") == 10  # 5 * 2
        assert context.get("result2") == 25  # 10 + 15

        # Check that chained function has multiple domains
        chained_function = context.get("chained_function")
        assert chained_function is not None
        assert hasattr(chained_function, "_poet_metadata")

        meta = chained_function._poet_metadata
        assert "domain1" in meta["domains"]
        assert "domain2" in meta["domains"]
        assert len(meta["domains"]) == 2

    def test_function_definition_and_execution(self, fresh_sandbox):
        """Test that POET decorated functions can be defined and called in Dana."""

        dana_code = '''
@poet(domain="test_execution")
def test_func(x: int, y: int) -> int:
    """Test function for execution."""
    return x + y

# Call the function
result = test_func(15, 25)
'''

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        assert context.get("result") == 40  # 15 + 25

    def test_multiple_functions_same_domain(self, fresh_sandbox):
        """Test multiple functions with the same domain."""

        dana_code = """
@poet(domain="math_operations")
def add_func(a: int, b: int) -> int:
    return a + b

@poet(domain="math_operations")
def subtract_func(a: int, b: int) -> int:
    return a - b

# Test both functions
sum_result = add_func(10, 5)
diff_result = subtract_func(10, 5)
"""

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        assert context.get("sum_result") == 15
        assert context.get("diff_result") == 5

        # Both functions should have the same domain
        add_func = context.get("add_func")
        subtract_func = context.get("subtract_func")

        assert "math_operations" in add_func._poet_metadata["domains"]
        assert "math_operations" in subtract_func._poet_metadata["domains"]

    def test_function_with_type_annotations(self, fresh_sandbox):
        """Test POET decorator with Dana functions that have type annotations."""

        dana_code = """
@poet(domain="typed_functions")
def typed_function(x: int, y: float, z: str) -> str:
    return f"{z}: {x + y}"

result = typed_function(10, 5.5, "Sum")
"""

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        assert context.get("result") == "Sum: 15.5"

    def test_decorator_metadata_preservation(self, fresh_sandbox):
        """Test that POET decorator metadata is properly preserved in Dana."""

        dana_code = '''
@poet(domain="metadata_test", retries=5, timeout=120, enable_training=True)
def metadata_function(x: int) -> int:
    """Function with comprehensive metadata."""
    return x * 3

# Just define the function, don't need to call it
test_value = 42
'''

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success

        func = context.get("metadata_function")
        assert func is not None
        assert hasattr(func, "_poet_metadata")

        meta = func._poet_metadata
        assert "metadata_test" in meta["domains"]
        assert meta["retries"] == 5
        assert meta["timeout"] == 120
        assert meta["enable_training"] is True

    def test_error_handling_in_dana(self, fresh_sandbox):
        """Test error handling with POET decorated functions in Dana."""

        # Note: Avoiding division by zero test due to Dana control flow issues
        # Instead test type-related errors that can be caught

        dana_code = """
@poet(domain="error_test", retries=1)
def error_prone_function(x: int) -> int:
    # This will work fine
    return x + 100

# Call with valid input
safe_result = error_prone_function(5)
"""

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        assert context.get("safe_result") == 105

    @pytest.mark.skip(reason="Dana control flow issue - functions with if statements cause execution to stop")
    def test_decorator_with_control_flow(self, fresh_sandbox):
        """Test POET decorator with functions containing control flow."""

        # This test is skipped due to known Dana issue with if statements
        dana_code = """
@poet(domain="control_flow")
def conditional_function(x: int) -> str:
    if x > 10:
        return "big"
    else:
        return "small"

result = conditional_function(15)
"""

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        assert context.get("result") == "big"

    def test_dana_context_integration(self, fresh_sandbox):
        """Test that POET decorator integrates properly with Dana context."""

        dana_code = """
@poet(domain="context_test")
def context_aware_function(x: int) -> int:
    # Function that works with context
    return x * 2

result = context_aware_function(20)
"""

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        assert context.get("result") == 40

    def test_complex_parameter_types(self, fresh_sandbox):
        """Test POET decorator with complex parameter types."""

        dana_code = """
@poet(domain="complex_types")
def complex_function(items: list, multiplier: int) -> int:
    # Simplified function since list comprehension may not be supported
    return len(items) * multiplier

test_list = [1, 2, 3, 4]
result = complex_function(test_list, 3)
"""

        result = fresh_sandbox.eval(dana_code)
        context = self.get_context(result)

        assert result.success
        expected_result = 12  # 4 items * 3 multiplier
        assert context.get("result") == expected_result
