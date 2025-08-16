"""
Test case function in Dana core library.
"""

import pytest

from dana.registry.function_registry import FunctionRegistry
from dana.core.lang.sandbox_context import SandboxContext
from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers


class TestCaseFunction:
    """Test case function registration and functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.registry = FunctionRegistry()
        register_py_wrappers(self.registry)
        self.context = SandboxContext()

    def test_case_function_registered(self):
        """Test that case function is properly registered."""
        # Check that case function is registered in the system namespace
        assert "case" in self.registry._functions["system"]

    def test_case_basic_functionality(self):
        """Test basic case function functionality."""
        func = self.registry._functions["system"]["case"][0]

        # Test with simple boolean conditions
        result = func.execute(self.context, (True, lambda: "first"), (False, lambda: "second"), lambda: "fallback")
        assert result == "first"

        result = func.execute(self.context, (False, lambda: "first"), (True, lambda: "second"), lambda: "fallback")
        assert result == "second"

        # Test fallback when no conditions match
        result = func.execute(self.context, (False, lambda: "first"), (False, lambda: "second"), lambda: "fallback")
        assert result == "fallback"

    def test_case_with_literal_values(self):
        """Test case function with literal values instead of functions."""
        func = self.registry._functions["system"]["case"][0]

        # Test with literal return values
        result = func.execute(self.context, (True, "literal_value"), (False, "other_value"), "default")
        assert result == "literal_value"

        result = func.execute(self.context, (False, "first"), (False, "second"), "default")
        assert result == "default"

    def test_case_with_value_conditions(self):
        """Test case function with value-based conditions."""
        func = self.registry._functions["system"]["case"][0]

        # Test with numeric conditions (simulating $$ comparisons)
        test_value = 42
        result = func.execute(
            self.context, (test_value == 42, lambda: "found_42"), (test_value > 100, lambda: "large_number"), lambda: "other"
        )
        assert result == "found_42"

        test_value = 150
        result = func.execute(
            self.context, (test_value == 42, lambda: "found_42"), (test_value > 100, lambda: "large_number"), lambda: "other"
        )
        assert result == "large_number"

    def test_case_with_string_conditions(self):
        """Test case function with string-based conditions."""
        func = self.registry._functions["system"]["case"][0]

        # Test with string conditions (simulating $$ == "value")
        test_type = "json"
        result = func.execute(
            self.context, (test_type == "json", lambda: "parse_json"), (test_type == "xml", lambda: "parse_xml"), lambda: "parse_default"
        )
        assert result == "parse_json"

        test_type = "yaml"
        result = func.execute(
            self.context, (test_type == "json", lambda: "parse_json"), (test_type == "xml", lambda: "parse_xml"), lambda: "parse_default"
        )
        assert result == "parse_default"

    def test_case_with_context_functions(self):
        """Test case function with functions that accept context."""
        func = self.registry._functions["system"]["case"][0]

        def context_func(context):
            return "used_context"

        def no_context_func():
            return "no_context"

        # Test with context-aware function
        result = func.execute(self.context, (True, context_func), (False, no_context_func), lambda: "fallback")
        assert result == "used_context"

        # Test with non-context function
        result = func.execute(self.context, (False, context_func), (True, no_context_func), lambda: "fallback")
        assert result == "no_context"

    def test_case_error_handling(self):
        """Test case function error handling."""
        func = self.registry._functions["system"]["case"][0]

        # Test with no arguments
        with pytest.raises(ValueError, match="case\\(\\) requires at least one argument"):
            func.execute(self.context)

        # Test with invalid tuple structure
        with pytest.raises(TypeError, match="Argument 1 must be a \\(condition, function\\) tuple"):
            func.execute(self.context, (True,), lambda: "fallback")

        # Test with no matching conditions and no fallback
        with pytest.raises(ValueError, match="No conditions matched.*no fallback function provided"):
            func.execute(self.context, (False, lambda: "never_reached"))

    def test_case_condition_evaluation_errors(self):
        """Test case function graceful handling of condition evaluation errors."""
        func = self.registry._functions["system"]["case"][0]

        def failing_condition():
            raise RuntimeError("Condition evaluation failed")

        # Should continue to next condition if one fails
        result = func.execute(
            self.context, (failing_condition, lambda: "failed_condition"), (True, lambda: "working_condition"), lambda: "fallback"
        )
        assert result == "working_condition"

    def test_case_multiple_conditions(self):
        """Test case function with many conditions."""
        func = self.registry._functions["system"]["case"][0]

        test_value = 5
        result = func.execute(
            self.context,
            (test_value == 1, lambda: "one"),
            (test_value == 2, lambda: "two"),
            (test_value == 3, lambda: "three"),
            (test_value == 4, lambda: "four"),
            (test_value == 5, lambda: "five"),
            (test_value == 6, lambda: "six"),
            lambda: "other",
        )
        assert result == "five"

    def test_case_with_callable_conditions(self):
        """Test case function with callable condition functions."""
        func = self.registry._functions["system"]["case"][0]

        def is_development():
            return True

        def is_production():
            return False

        result = func.execute(
            self.context, (is_development, lambda: "dev_handler"), (is_production, lambda: "prod_handler"), lambda: "default_handler"
        )
        assert result == "dev_handler"

    def test_case_nested_scenarios(self):
        """Test case function in nested scenarios."""
        func = self.registry._functions["system"]["case"][0]

        def inner_case():
            return func.execute(self.context, (True, lambda: "inner_result"), lambda: "inner_fallback")

        # Test case function returning result of another case function
        result = func.execute(self.context, (True, inner_case), lambda: "outer_fallback")
        assert result == "inner_result"
