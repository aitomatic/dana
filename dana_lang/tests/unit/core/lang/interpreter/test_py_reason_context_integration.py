"""
Integration tests for py_reason() with enhanced context detection.

These tests verify that py_reason() correctly uses the new get_execution_stack()
functionality to detect context from comments, docstrings, and AST nodes.
"""

import unittest
from unittest.mock import Mock, patch

from dana.core.lang.sandbox_context import SandboxContext
from dana.libs.corelib.py_wrappers.py_reason import py_reason


class TestPyReasonContextIntegration(unittest.TestCase):
    """Test py_reason() integration with enhanced context detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = SandboxContext()

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_with_typed_assignment(self, mock_old_reason):
        """Test py_reason() detects typed assignment context."""
        # Mock the old reason function to return a simple string
        mock_old_reason.return_value = "test response"

        # Create a mock assignment node with type hint
        from dana.core.lang.ast import Assignment, TypeHint

        assignment_node = Mock(spec=Assignment)
        assignment_node.type_hint = Mock(spec=TypeHint)
        assignment_node.type_hint.name = "str"

        # Add to execution stack
        from dana.core.lang.interpreter.error_context import ExecutionLocation

        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=assignment_node)
        self.context._error_context.execution_stack.append(location)

        # Call py_reason
        result = py_reason(self.context, "What is the weather?")

        # Verify that context detection was attempted
        self.assertEqual(result, "test response")
        # The mock should have been called with enhanced prompt
        mock_old_reason.assert_called_once()
        call_args = mock_old_reason.call_args
        self.assertIn("What is the weather?", call_args[0][1])  # Prompt should be enhanced

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_with_metadata_comment(self, mock_old_reason):
        """Test py_reason() detects metadata comment context."""
        # Mock the old reason function
        mock_old_reason.return_value = "test response"

        # Create a mock node with metadata comment
        mock_node = Mock()
        mock_node.metadata = {"comment": "returns a string value"}

        # Add to execution stack
        from dana.core.lang.interpreter.error_context import ExecutionLocation

        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=mock_node)
        self.context._error_context.execution_stack.append(location)

        # Call py_reason
        result = py_reason(self.context, "Process this data")

        # Verify result
        self.assertEqual(result, "test response")
        mock_old_reason.assert_called_once()

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_with_docstring(self, mock_old_reason):
        """Test py_reason() detects docstring context."""
        # Mock the old reason function
        mock_old_reason.return_value = "test response"

        # Create a mock function definition with docstring
        from dana.core.lang.ast import FunctionDefinition

        func_def = Mock(spec=FunctionDefinition)
        func_def.docstring = "Returns: dict"

        # Add to execution stack
        from dana.core.lang.interpreter.error_context import ExecutionLocation

        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=func_def)
        self.context._error_context.execution_stack.append(location)

        # Call py_reason
        result = py_reason(self.context, "Analyze this data")

        # Verify result
        self.assertEqual(result, "test response")
        mock_old_reason.assert_called_once()

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_with_field_comment(self, mock_old_reason):
        """Test py_reason() detects field comment context."""
        # Mock the old reason function
        mock_old_reason.return_value = "test response"

        # Create a mock struct field with comment
        from dana.core.lang.ast import StructField

        field = Mock(spec=StructField)
        field.comment = "user's age in years"

        # Add to execution stack
        from dana.core.lang.interpreter.error_context import ExecutionLocation

        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=field)
        self.context._error_context.execution_stack.append(location)

        # Call py_reason
        result = py_reason(self.context, "Get user age")

        # Verify result
        self.assertEqual(result, "test response")
        mock_old_reason.assert_called_once()

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_priority_order(self, mock_old_reason):
        """Test py_reason() respects priority order in context detection."""
        # Mock the old reason function
        mock_old_reason.return_value = "test response"

        # Create multiple nodes with different context types
        from dana.core.lang.ast import Assignment, TypeHint

        assignment_node = Mock(spec=Assignment)
        assignment_node.type_hint = Mock(spec=TypeHint)
        assignment_node.type_hint.name = "int"

        metadata_node = Mock()
        metadata_node.metadata = {"comment": "returns string"}

        # Add to execution stack (assignment should be detected first)
        from dana.core.lang.interpreter.error_context import ExecutionLocation

        location1 = ExecutionLocation(ast_node=metadata_node)  # Lower priority
        location2 = ExecutionLocation(ast_node=assignment_node)  # Higher priority

        self.context._error_context.execution_stack.extend([location1, location2])

        # Call py_reason
        result = py_reason(self.context, "Calculate value")

        # Verify result
        self.assertEqual(result, "test response")
        mock_old_reason.assert_called_once()

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_fallback_when_no_context(self, mock_old_reason):
        """Test py_reason() falls back gracefully when no context is detected."""
        # Mock the old reason function
        mock_old_reason.return_value = "test response"

        # Empty execution stack
        self.context._error_context.execution_stack = []

        # Call py_reason
        result = py_reason(self.context, "Simple question")

        # Verify result
        self.assertEqual(result, "test response")
        mock_old_reason.assert_called_once()

    @patch("dana.libs.corelib.py_wrappers.py_reason._execute_reason_call")
    def test_py_reason_with_assignment_type_fallback(self, mock_old_reason):
        """Test py_reason() uses assignment type as fallback."""
        # Mock the old reason function
        mock_old_reason.return_value = "test response"

        # Set assignment type in context
        self.context.set("system:__current_assignment_type", "str")

        # Empty execution stack
        self.context._error_context.execution_stack = []

        # Call py_reason
        result = py_reason(self.context, "Get user input")

        # Verify result
        self.assertEqual(result, "test response")
        mock_old_reason.assert_called_once()

    def test_get_execution_stack_returns_list(self):
        """Test that get_execution_stack() returns a list."""
        stack = self.context.get_execution_stack()
        self.assertIsInstance(stack, list)

    def test_get_current_node_returns_node_or_none(self):
        """Test that get_current_node() returns node or None."""
        # Empty stack
        node = self.context.get_current_node()
        self.assertIsNone(node)

        # Add a node to stack
        from dana.core.lang.interpreter.error_context import ExecutionLocation

        mock_node = Mock()
        location = ExecutionLocation(ast_node=mock_node)
        self.context._error_context.execution_stack.append(location)

        # Should return the node
        node = self.context.get_current_node()
        self.assertEqual(node, mock_node)


if __name__ == "__main__":
    unittest.main()
