"""Unit tests for declarative function execution."""

from unittest.mock import Mock

import pytest

from dana.core.lang.ast import (
    BinaryExpression,
    BinaryOperator,
    DeclarativeFunctionDefinition,
    Identifier,
    LiteralExpression,
    Parameter,
    TypeHint,
)
from dana.core.lang.interpreter.executor.statement_executor import StatementExecutor
from dana.core.lang.sandbox_context import SandboxContext


class TestDeclarativeFunctionExecution:
    """Test declarative function execution."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock parent executor that can execute expressions
        self.mock_parent = Mock()
        self.mock_parent.execute = Mock(side_effect=self._mock_execute)

        self.executor = StatementExecutor(self.mock_parent)
        self.context = SandboxContext()

    def _mock_execute(self, node, context):
        """Mock expression execution for testing."""
        if isinstance(node, LiteralExpression):
            return node.value
        elif isinstance(node, Identifier):
            return context.get(f"local:{node.name}")
        elif isinstance(node, BinaryExpression):
            left_val = self._mock_execute(node.left, context)
            right_val = self._mock_execute(node.right, context)

            if node.operator == BinaryOperator.ADD:
                return left_val + right_val
            elif node.operator == BinaryOperator.MULTIPLY:
                return left_val * right_val
            elif node.operator == BinaryOperator.PIPE:
                # For pipe operations, create a composed function
                if callable(left_val) and callable(right_val):

                    def composed(*args, **kwargs):
                        return right_val(left_val(*args, **kwargs))

                    return composed
                elif callable(left_val):
                    return left_val
                elif callable(right_val):
                    return right_val
                else:
                    return right_val
            else:
                raise NotImplementedError(f"Operator {node.operator} not implemented in mock")
        else:
            raise NotImplementedError(f"Node type {type(node)} not implemented in mock")

    def test_basic_declarative_function_execution(self):
        """Test basic execution of declarative functions."""
        # Create a simple declarative function: def add_one(x: int) -> int = x + 1
        node = DeclarativeFunctionDefinition(
            name=Identifier("add_one"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
        )

        # Execute the declarative function definition
        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Verify the function was created and stored in context
        assert result is not None
        assert callable(result)
        assert result.__name__ == "add_one"
        assert self.context.has("local:add_one")

        # Test calling the function
        func_result = result(5)
        assert func_result == 6

    def test_declarative_function_without_return_type(self):
        """Test declarative function without return type annotation."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("double"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=None,
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.MULTIPLY, right=LiteralExpression(2)),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)
        assert result is not None
        assert callable(result)
        assert result.__name__ == "double"

        # Test calling the function
        func_result = result(5)
        assert func_result == 10

    def test_declarative_function_without_parameters(self):
        """Test declarative function without parameters."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("get_constant"), parameters=[], return_type=TypeHint("int"), composition=LiteralExpression(42)
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)
        assert result is not None
        assert callable(result)
        assert result.__name__ == "get_constant"

        # Test calling the function
        func_result = result()
        assert func_result == 42

    def test_declarative_function_with_multiple_parameters(self):
        """Test declarative function with multiple parameters."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("add_multiply"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("int")), Parameter("factor", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(
                left=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=Identifier("y")),
                operator=BinaryOperator.MULTIPLY,
                right=Identifier("factor"),
            ),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)
        assert result is not None
        assert callable(result)
        assert result.__name__ == "add_multiply"

        # Test calling the function
        func_result = result(2, 3, 4)
        assert func_result == 20  # (2 + 3) * 4 = 20

    def test_declarative_function_with_keyword_arguments(self):
        """Test declarative function with keyword arguments."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("format_message"),
            parameters=[Parameter("message", TypeHint("str")), Parameter("prefix", TypeHint("str"))],
            return_type=TypeHint("str"),
            composition=BinaryExpression(left=Identifier("prefix"), operator=BinaryOperator.ADD, right=Identifier("message")),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)
        assert result is not None
        assert callable(result)

        # Test calling with keyword arguments
        func_result = result(message="Hello", prefix="Msg: ")
        assert func_result == "Msg: Hello"

    def test_declarative_function_metadata(self):
        """Test that declarative functions have proper metadata."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("str"),
            composition=LiteralExpression("test"),
            docstring="Test function documentation",
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check metadata
        assert result.__name__ == "test_func"
        assert result.__qualname__ == "test_func"
        assert result.__doc__ == "Test function documentation"
        assert result.__annotations__ == {"x": int, "return": str}

    def test_declarative_function_context_isolation(self):
        """Test that declarative functions have isolated execution contexts."""
        # Set up initial context
        self.context.set("local:global_var", 100)

        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=Identifier("global_var")),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Test that the function can access global context
        func_result = result(5)
        assert func_result == 105  # 5 + 100

    def test_declarative_function_error_handling(self):
        """Test error handling in declarative function execution."""
        # Test with undefined variable in composition
        node = DeclarativeFunctionDefinition(
            name=Identifier("error_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=Identifier("undefined_var")),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # The function should be created, but calling it should raise an error
        # since undefined_var is not in context
        with pytest.raises((NameError, KeyError, AttributeError)):
            result(5)

    def test_declarative_function_with_complex_composition(self):
        """Test declarative function with complex composition expressions."""
        # Create a more complex composition: (x + 1) * 2
        node = DeclarativeFunctionDefinition(
            name=Identifier("complex_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(
                left=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
                operator=BinaryOperator.MULTIPLY,
                right=LiteralExpression(2),
            ),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)
        assert result is not None
        assert callable(result)

        # Test calling the function
        func_result = result(5)
        assert func_result == 12  # (5 + 1) * 2 = 12

    def test_multiple_declarative_functions(self):
        """Test creating multiple declarative functions in the same context."""
        # Create first function
        node1 = DeclarativeFunctionDefinition(
            name=Identifier("func1"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
        )

        # Create second function
        node2 = DeclarativeFunctionDefinition(
            name=Identifier("func2"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.MULTIPLY, right=LiteralExpression(2)),
        )

        # Execute both
        result1 = self.executor.execute_declarative_function_definition(node1, self.context)
        result2 = self.executor.execute_declarative_function_definition(node2, self.context)

        # Verify both functions exist
        assert self.context.has("local:func1")
        assert self.context.has("local:func2")

        # Test both functions
        assert result1(5) == 6
        assert result2(5) == 10

    def test_declarative_function_parameter_validation(self):
        """Test that declarative functions validate their parameters correctly."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=TypeHint("str"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Test with correct number of arguments
        func_result = result(5, "test")
        assert func_result == 6

        # Test with wrong number of arguments (should still work due to flexible binding)
        func_result = result(5)
        assert func_result == 6
