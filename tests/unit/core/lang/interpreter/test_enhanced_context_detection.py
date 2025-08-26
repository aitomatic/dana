"""
Tests for enhanced context detection with execution stack support.

This module tests the new get_execution_stack() functionality and enhanced
context detection that can see comments, docstrings, and AST nodes.
"""

import unittest
from unittest.mock import Mock

from dana.core.lang.ast import Assignment, FunctionCall, FunctionDefinition, StructField, TypeHint
from dana.core.lang.interpreter.context_detection import ContextDetector, ContextType
from dana.core.lang.interpreter.error_context import ExecutionLocation
from dana.core.lang.sandbox_context import SandboxContext


class TestEnhancedContextDetection(unittest.TestCase):
    """Test enhanced context detection with execution stack support."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = ContextDetector()
        self.context = Mock(spec=SandboxContext)

    def test_get_execution_stack_method_exists(self):
        """Test that SandboxContext has get_execution_stack method."""
        context = SandboxContext()
        self.assertTrue(hasattr(context, "get_execution_stack"))
        self.assertTrue(callable(context.get_execution_stack))

    def test_get_current_node_method_exists(self):
        """Test that SandboxContext has get_current_node method."""
        context = SandboxContext()
        self.assertTrue(hasattr(context, "get_current_node"))
        self.assertTrue(callable(context.get_current_node))

    def test_execution_location_with_ast_node(self):
        """Test that ExecutionLocation can store AST nodes."""
        mock_node = Mock()
        location = ExecutionLocation(filename="test.na", line=10, column=5, function_name="test_function", ast_node=mock_node)

        self.assertEqual(location.ast_node, mock_node)
        self.assertEqual(location.filename, "test.na")
        self.assertEqual(location.line, 10)

    def test_detect_typed_assignment_from_stack(self):
        """Test detecting typed assignment from execution stack."""
        # Create a mock assignment node with type hint
        assignment_node = Mock()
        assignment_node.__class__ = Assignment  # Make isinstance work
        assignment_node.type_hint = Mock()
        assignment_node.type_hint.__class__ = TypeHint  # Make isinstance work for type_hint
        assignment_node.type_hint.name = "str"

        # Create execution location with AST node
        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=assignment_node)

        # Mock context with execution stack and no assignment type
        context = Mock()
        context.get_execution_stack.return_value = [location]
        context.get.return_value = None  # No assignment type set

        # Test detection
        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.expected_type, "str")
        self.assertEqual(result.context_type, ContextType.ASSIGNMENT)
        self.assertEqual(result.confidence, 1.0)

    def test_detect_function_call_from_stack(self):
        """Test detecting function call from execution stack."""
        # Create a mock function call node
        func_call_node = Mock()
        func_call_node.__class__ = FunctionCall  # Make isinstance work
        func_call_node.name = "cast"
        func_call_node.args = [Mock(), Mock()]  # type and value arguments

        # Create execution location with AST node
        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=func_call_node)

        # Mock context with execution stack and no assignment type
        context = Mock()
        context.get_execution_stack.return_value = [location]
        context.get.return_value = None  # No assignment type set

        # Test detection
        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.context_type, ContextType.FUNCTION_CALL)

    def test_detect_metadata_comment_from_stack(self):
        """Test detecting metadata comment from execution stack."""
        # Create a mock node with metadata comment
        mock_node = Mock()
        mock_node.metadata = {"comment": "returns a string value"}

        # Create execution location with AST node
        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=mock_node)

        # Mock context with execution stack and no assignment type
        context = Mock()
        context.get_execution_stack.return_value = [location]
        context.get.return_value = None  # No assignment type set

        # Test detection
        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.expected_type, "str")
        self.assertEqual(result.context_type, ContextType.EXPRESSION)
        self.assertEqual(result.confidence, 0.8)
        self.assertEqual(result.metadata["source"], "metadata_comment")

    def test_detect_docstring_from_stack(self):
        """Test detecting docstring from execution stack."""
        # Create a mock function definition with docstring
        func_def = Mock(spec=FunctionDefinition)
        func_def.docstring = "Returns: str"

        # Create execution location with AST node
        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=func_def)

        # Mock context with execution stack and no assignment type
        context = Mock()
        context.get_execution_stack.return_value = [location]
        context.get.return_value = None  # No assignment type set

        # Test detection
        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.expected_type, "str")
        self.assertEqual(result.context_type, ContextType.RETURN_VALUE)
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.metadata["source"], "docstring")

    def test_detect_field_comment_from_stack(self):
        """Test detecting field comment from execution stack."""
        # Create a mock struct field with comment
        field = Mock()
        field.__class__ = StructField  # Make isinstance work
        field.configure_mock(comment="user's age in years")  # Configure the mock to return the string

        # Create execution location with AST node
        location = ExecutionLocation(filename="test.na", line=5, column=1, function_name="test_function", ast_node=field)

        # Mock context with execution stack and no assignment type
        context = Mock()
        context.get_execution_stack.return_value = [location]
        context.get.return_value = None  # No assignment type set

        # Test detection
        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.expected_type, "int")  # "years" maps to int
        self.assertEqual(result.context_type, ContextType.EXPRESSION)
        self.assertEqual(result.confidence, 0.7)
        self.assertEqual(result.metadata["source"], "field_comment")

    def test_priority_order_in_stack_analysis(self):
        """Test that higher priority contexts are detected first."""
        # Create multiple nodes with different context types
        assignment_node = Mock()
        assignment_node.__class__ = Assignment  # Make isinstance work
        assignment_node.type_hint = Mock()
        assignment_node.type_hint.__class__ = TypeHint  # Make isinstance work for type_hint
        assignment_node.type_hint.name = "int"

        func_call_node = Mock()
        func_call_node.__class__ = FunctionCall  # Make isinstance work
        func_call_node.name = "cast"
        func_call_node.args = [Mock(), Mock()]

        metadata_node = Mock()
        metadata_node.metadata = {"comment": "returns string"}

        # Create execution locations (assignment should be detected first)
        location1 = ExecutionLocation(ast_node=metadata_node)  # Lower priority
        location2 = ExecutionLocation(ast_node=func_call_node)  # Medium priority
        location3 = ExecutionLocation(ast_node=assignment_node)  # Highest priority

        # Mock context with execution stack (most recent first) and no assignment type
        context = Mock()
        context.get_execution_stack.return_value = [location1, location2, location3]
        context.get.return_value = None  # No assignment type set

        # Test detection - should return assignment context (highest priority)
        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.expected_type, "int")
        self.assertEqual(result.context_type, ContextType.ASSIGNMENT)

    def test_type_extraction_from_comments(self):
        """Test extracting type information from various comment patterns."""
        test_cases = [
            ("returns a string", "str"),
            ("should return dict", "dict"),
            ("type: int", "int"),
            ("string type", "str"),
            ("float value", "float"),
            ("boolean data", "bool"),
            ("list value", "list"),
        ]

        for comment, expected_type in test_cases:
            with self.subTest(comment=comment):
                result = self.detector._extract_type_from_comment(comment)
                self.assertEqual(result, expected_type)

    def test_type_extraction_from_docstrings(self):
        """Test extracting type information from various docstring patterns."""
        test_cases = [
            ("Returns: str", "str"),
            ("Return type dict", "dict"),
            ("-> int", "int"),
            ("returns: float", "float"),
        ]

        for docstring, expected_type in test_cases:
            with self.subTest(docstring=docstring):
                result = self.detector._extract_type_from_docstring(docstring)
                self.assertEqual(result, expected_type)

    def test_no_context_when_stack_empty(self):
        """Test that no context is detected when execution stack is empty."""
        context = Mock()
        context.get_execution_stack.return_value = []
        context.get.return_value = None  # No assignment type set

        result = self.detector.detect_type_context(context)

        self.assertIsNone(result)

    def test_no_context_when_no_ast_nodes(self):
        """Test that no context is detected when AST nodes are missing."""
        location = ExecutionLocation(
            filename="test.na",
            line=5,
            column=1,
            function_name="test_function",
            ast_node=None,  # No AST node
        )

        context = Mock()
        context.get_execution_stack.return_value = [location]
        context.get.return_value = None  # No assignment type set

        result = self.detector.detect_type_context(context)

        self.assertIsNone(result)

    def test_fallback_to_assignment_type(self):
        """Test fallback to assignment type when stack analysis fails."""
        context = Mock()
        context.get_execution_stack.return_value = []
        context.get.return_value = "str"  # Assignment type

        result = self.detector.detect_type_context(context)

        self.assertIsNotNone(result)
        self.assertEqual(result.expected_type, "str")
        self.assertEqual(result.context_type, ContextType.ASSIGNMENT)
        self.assertEqual(result.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
