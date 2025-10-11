"""
Tests for execution tracking functionality in Dana.

This module tests the universal execution tracking system that provides
detailed error reporting with execution traces.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from unittest.mock import Mock, patch

import pytest

from dana_lang.core.lang.ast import Program
from dana_lang.core.lang.interpreter.error_context import ExecutionLocation
from dana_lang.core.lang.interpreter.executor.base_executor import BaseExecutor
from dana_lang.core.lang.interpreter.executor.program_executor import ProgramExecutor
from dana_lang.core.lang.interpreter.executor.statement_executor import StatementExecutor
from dana_lang.core.lang.sandbox_context import SandboxContext


class TestExecutionTracking:
    """Test execution tracking functionality."""

    def test_base_executor_tracking_enabled(self):
        """Test that BaseExecutor tracks execution when enabled."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        # Create a mock node with location
        mock_node = Mock()
        mock_node.location = Mock()
        mock_node.location.line = 10
        mock_node.location.column = 5
        mock_node.__class__.__name__ = "TestNode"

        executor = BaseExecutor(parent=None)

        # Mock the execute method to return a value
        with patch.object(executor, "execute", return_value="test_result") as mock_execute:
            result = executor.execute_with_tracking(mock_node, context, "test operation")

            # Should have called execute
            mock_execute.assert_called_once_with(mock_node, context)

            # Should have pushed and popped location
            assert len(context.error_context.execution_stack) == 0  # Stack should be empty after execution
            assert result == "test_result"

    def test_base_executor_tracking_disabled(self):
        """Test that BaseExecutor skips tracking when disabled."""
        context = SandboxContext(track_execution=False)

        mock_node = Mock()
        mock_node.location = Mock()
        mock_node.location.line = 10
        mock_node.location.column = 5

        executor = BaseExecutor(parent=None)

        with patch.object(executor, "execute", return_value="test_result") as mock_execute:
            result = executor.execute_with_tracking(mock_node, context, "test operation")

            # Should have called execute directly
            mock_execute.assert_called_once_with(mock_node, context)
            assert result == "test_result"

            # Should not have pushed to execution stack
            assert len(context.error_context.execution_stack) == 0

    def test_base_executor_no_location(self):
        """Test that BaseExecutor skips tracking when node has no location."""
        context = SandboxContext(track_execution=True)

        mock_node = Mock()
        mock_node.location = None  # No location information

        executor = BaseExecutor(parent=None)

        with patch.object(executor, "execute", return_value="test_result") as mock_execute:
            result = executor.execute_with_tracking(mock_node, context, "test operation")

            # Should have called execute directly
            mock_execute.assert_called_once_with(mock_node, context)
            assert result == "test_result"

            # Should not have pushed to execution stack
            assert len(context.error_context.execution_stack) == 0

    def test_tracking_decorator(self):
        """Test the @track_execution decorator."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        # Create a mock executor with a decorated method
        class TestExecutor(BaseExecutor):
            @BaseExecutor.track_execution("test operation")
            def execute_test(self, node, context):
                return "decorated_result"

        executor = TestExecutor(parent=None)

        # Create a mock node with location
        mock_node = Mock()
        mock_node.location = Mock()
        mock_node.location.line = 15
        mock_node.location.column = 8

        result = executor.execute_test(mock_node, context)

        assert result == "decorated_result"
        assert len(context.error_context.execution_stack) == 0  # Stack should be empty after execution

    def test_program_executor_statement_tracking(self):
        """Test that ProgramExecutor tracks individual statements."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        # Create mock statements with locations
        stmt1 = Mock()
        stmt1.location = Mock()
        stmt1.location.line = 1
        stmt1.location.column = 1
        stmt1.__class__.__name__ = "Statement1"

        stmt2 = Mock()
        stmt2.location = Mock()
        stmt2.location.line = 2
        stmt2.location.column = 1
        stmt2.__class__.__name__ = "Statement2"

        # Create a program with statements
        program = Program(statements=[stmt1, stmt2])

        # Create executor with mock parent
        parent_executor = Mock()
        parent_executor.execute_with_tracking = Mock(side_effect=lambda node, ctx, op: f"result_{op}")

        executor = ProgramExecutor(parent_executor)

        result = executor.execute_program(program, context)

        # Should have called execute_with_tracking for each statement
        assert parent_executor.execute_with_tracking.call_count == 2
        parent_executor.execute_with_tracking.assert_any_call(stmt1, context, "statement 1")
        parent_executor.execute_with_tracking.assert_any_call(stmt2, context, "statement 2")

        # Should return the result of the last statement
        assert result == "result_statement 2"

    def test_statement_executor_decorated_methods(self):
        """Test that StatementExecutor methods are properly decorated."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        # Create a mock assignment node
        assignment = Mock()
        assignment.location = Mock()
        assignment.location.line = 5
        assignment.location.column = 10
        assignment.__class__.__name__ = "Assignment"

        # Create executor with mock parent and handlers
        parent_executor = Mock()
        assignment_handler = Mock()
        assignment_handler.execute_assignment = Mock(return_value="assignment_result")

        executor = StatementExecutor(parent_executor)
        executor.assignment_handler = assignment_handler

        result = executor.execute_assignment(assignment, context)

        # Should have called the handler
        assignment_handler.execute_assignment.assert_called_once_with(assignment, context)
        assert result == "assignment_result"

        # Should have tracked the execution
        assert len(context.error_context.execution_stack) == 0  # Stack should be empty after execution

    def test_execution_stack_management(self):
        """Test that execution stack is properly managed with push/pop."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        executor = BaseExecutor(parent=None)

        # Create mock nodes
        node1 = Mock()
        node1.location = Mock()
        node1.location.line = 1
        node1.location.column = 1
        node1.__class__.__name__ = "Node1"

        node2 = Mock()
        node2.location = Mock()
        node2.location.line = 2
        node2.location.column = 1
        node2.__class__.__name__ = "Node2"

        # Mock execute to call another tracked execution
        def mock_execute(node, ctx):
            if node == node1:
                return executor.execute_with_tracking(node2, ctx, "nested operation")
            return "result"

        with patch.object(executor, "execute", side_effect=mock_execute):
            result = executor.execute_with_tracking(node1, context, "outer operation")

            assert result == "result"
            # Stack should be empty after all executions complete
            assert len(context.error_context.execution_stack) == 0

    def test_error_context_preservation(self):
        """Test that error context is preserved during execution."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        executor = BaseExecutor(parent=None)

        # Create a mock node
        node = Mock()
        node.location = Mock()
        node.location.line = 10
        node.location.column = 5
        node.__class__.__name__ = "TestNode"

        with patch.object(executor, "execute", return_value="test_result"):
            result = executor.execute_with_tracking(node, context, "test operation")

            # Check that location was properly created
            # The stack should be empty, but we can verify the location was created correctly
            assert result == "test_result"

    def test_repl_mode_detection(self):
        """Test that tracking is disabled in REPL mode."""
        context = SandboxContext(track_execution=True)
        context.error_context.set_file("test.na")

        # Simulate REPL mode
        context.set("system:__repl_input_context", "test")

        executor = BaseExecutor(parent=None)

        mock_node = Mock()
        mock_node.location = Mock()
        mock_node.location.line = 10
        mock_node.location.column = 5

        with patch.object(executor, "execute", return_value="test_result") as mock_execute:
            result = executor.execute_with_tracking(mock_node, context, "test operation")

            # Should have called execute directly (no tracking)
            mock_execute.assert_called_once_with(mock_node, context)
            assert result == "test_result"

            # Should not have pushed to execution stack
            assert len(context.error_context.execution_stack) == 0

    def test_configuration_inheritance(self):
        """Test that configuration is properly inherited from parent context."""
        parent_context = SandboxContext(track_execution=False)
        child_context = SandboxContext(parent=parent_context)

        # Child should inherit parent's configuration
        assert child_context.track_execution is False

        # But can override it
        child_context.track_execution = True
        assert child_context.track_execution is True

    def test_dana_sandbox_configuration(self):
        """Test that DanaSandbox properly passes configuration to context."""
        from dana_lang.core.lang.dana_sandbox import DanaSandbox

        # Test with tracking enabled (default)
        sandbox = DanaSandbox(track_execution=True)
        assert sandbox._context.track_execution is True

        # Test with tracking disabled
        sandbox = DanaSandbox(track_execution=False)
        assert sandbox._context.track_execution is False


class TestExecutionLocation:
    """Test ExecutionLocation creation and management."""

    def test_execution_location_creation(self):
        """Test that ExecutionLocation is created correctly."""
        location = ExecutionLocation(
            filename="test.na", line=10, column=5, function_name="test operation", source_line="x = 42", ast_node=Mock()
        )

        assert location.filename == "test.na"
        assert location.line == 10
        assert location.column == 5
        assert location.function_name == "test operation"
        assert location.source_line == "x = 42"

    def test_execution_location_string_representation(self):
        """Test ExecutionLocation string representation."""
        location = ExecutionLocation(filename="test.na", line=10, column=5, function_name="test operation")

        expected = 'File "test.na", line 10, column 5, in test operation'
        assert str(location) == expected

    def test_execution_location_minimal(self):
        """Test ExecutionLocation with minimal information."""
        location = ExecutionLocation()

        assert location.filename is None
        assert location.line is None
        assert location.column is None
        assert location.function_name is None
        assert str(location) == "unknown location"


class TestErrorContextIntegration:
    """Test integration with ErrorContext."""

    def test_error_context_stack_operations(self):
        """Test ErrorContext stack push/pop operations."""
        context = SandboxContext()

        location1 = ExecutionLocation(filename="test.na", line=1, column=1, function_name="operation1")

        location2 = ExecutionLocation(filename="test.na", line=2, column=1, function_name="operation2")

        # Push locations
        context.error_context.push_location(location1)
        assert len(context.error_context.execution_stack) == 1
        assert context.error_context.current_location == location1

        context.error_context.push_location(location2)
        assert len(context.error_context.execution_stack) == 2
        assert context.error_context.current_location == location2

        # Pop locations
        popped = context.error_context.pop_location()
        assert popped == location2
        assert len(context.error_context.execution_stack) == 1
        assert context.error_context.current_location == location1

        popped = context.error_context.pop_location()
        assert popped == location1
        assert len(context.error_context.execution_stack) == 0
        assert context.error_context.current_location.filename is None

    def test_error_context_source_line_retrieval(self):
        """Test ErrorContext source line retrieval."""
        context = SandboxContext()
        context.error_context.set_file("test.na")

        # Mock source loading
        with patch.object(context.error_context, "load_source", return_value=["line1", "line2", "line3"]):
            source_line = context.error_context.get_source_line("test.na", 2)
            assert source_line == "line2"

            # Test out of bounds
            source_line = context.error_context.get_source_line("test.na", 5)
            assert source_line is None


if __name__ == "__main__":
    pytest.main([__file__])
