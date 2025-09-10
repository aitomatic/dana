"""
Tests for default parameter evaluation in Dana function definitions.

This module tests that default parameters with complex types (like lists, dicts, etc.)
are properly evaluated to their corresponding Python objects instead of being
converted to string representations of AST nodes.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from unittest.mock import MagicMock

import pytest

from dana.core.lang.ast import DictLiteral, ListLiteral, LiteralExpression
from dana.core.lang.interpreter.executor.function_executor import FunctionExecutor
from dana.core.lang.sandbox_context import SandboxContext


class TestDefaultParameterEvaluation:
    """Test cases for default parameter evaluation in function definitions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = SandboxContext()
        self.parent_executor = MagicMock()
        self.function_executor = FunctionExecutor(self.parent_executor)

    def test_empty_list_default_parameter_evaluation(self):
        """Test that empty list default parameters are evaluated to actual Python lists."""
        empty_list_literal = ListLiteral(items=[])

        # Mock the parent executor to return proper evaluation
        self.parent_executor._expression_executor.execute.return_value = []
        self.parent_executor.execute.return_value = []

        result = self.function_executor._evaluate_expression(empty_list_literal, self.context)

        # Should return actual empty list, not string representation
        assert isinstance(result, list)
        assert result == []
        assert result != "ListLiteral(items=[], location=None)"

    def test_list_with_items_default_parameter_evaluation(self):
        """Test that list default parameters with items are evaluated correctly."""
        list_literal = ListLiteral(items=[LiteralExpression(value=1), LiteralExpression(value="test")])

        # Mock evaluation to return actual list
        self.parent_executor._expression_executor.execute.return_value = [1, "test"]
        self.parent_executor.execute.return_value = [1, "test"]

        result = self.function_executor._evaluate_expression(list_literal, self.context)

        assert isinstance(result, list)
        assert result == [1, "test"]

    def test_empty_dict_default_parameter_evaluation(self):
        """Test that empty dict default parameters are evaluated correctly."""
        empty_dict_literal = DictLiteral(items=[])

        self.parent_executor._expression_executor.execute.return_value = {}
        self.parent_executor.execute.return_value = {}

        result = self.function_executor._evaluate_expression(empty_dict_literal, self.context)

        assert isinstance(result, dict)
        assert result == {}
        assert result != "DictLiteral(items=[], location=None)"

    def test_uses_expression_executor_when_available(self):
        """Test that _expression_executor is preferred when available."""
        # Mock both execute methods
        self.parent_executor._expression_executor = MagicMock()
        self.parent_executor._expression_executor.execute.return_value = []
        self.parent_executor.execute.return_value = "should not be called"

        empty_list_literal = ListLiteral(items=[])
        result = self.function_executor._evaluate_expression(empty_list_literal, self.context)

        # Should use expression_executor.execute_expression
        self.parent_executor._expression_executor.execute.assert_called_once()
        self.parent_executor.execute.assert_not_called()
        assert result == []

    def test_fallback_to_main_executor(self):
        """Test fallback to main executor when expression_executor not available."""
        # Remove _expression_executor to test fallback
        if hasattr(self.parent_executor, "_expression_executor"):
            del self.parent_executor._expression_executor

        # Only provide main execute method
        self.parent_executor.execute.return_value = []

        empty_list_literal = ListLiteral(items=[])
        result = self.function_executor._evaluate_expression(empty_list_literal, self.context)

        self.parent_executor.execute.assert_called_once_with(empty_list_literal, self.context)
        assert result == []

    def test_error_when_no_executor_available(self):
        """Test that clear error is raised when no executor is available."""
        # Remove both execute methods
        if hasattr(self.parent_executor, "execute"):
            del self.parent_executor.execute
        if hasattr(self.parent_executor, "_expression_executor"):
            del self.parent_executor._expression_executor

        empty_list_literal = ListLiteral(items=[])

        with pytest.raises(ValueError, match="Cannot evaluate expression: no executor available"):
            self.function_executor._evaluate_expression(empty_list_literal, self.context)


if __name__ == "__main__":
    pytest.main([__file__])
