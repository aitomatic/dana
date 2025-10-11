"""
Unit tests for declarative function execution.

Tests the execution of declarative function definitions with various parameter configurations.
"""

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
from dana.core.lang.interpreter.executor.base_executor import BaseExecutor
from dana.core.lang.interpreter.executor.statement_executor import StatementExecutor
from dana.core.lang.sandbox_context import SandboxContext
from dana.registry.function_registry import FunctionRegistry


class TestDeclarativeFunctionExecution:
    """Test cases for declarative function execution."""

    @pytest.fixture
    def executor(self):
        """Create a statement executor for testing."""

        class MockParentExecutor(BaseExecutor):
            def __init__(self):
                super().__init__(parent=None)

            def execute(self, node, context):
                if isinstance(node, Identifier):
                    return context.get(f"local:{node.name}")
                elif isinstance(node, LiteralExpression):
                    return node.value
                elif isinstance(node, BinaryExpression):
                    left = self.execute(node.left, context)
                    right = self.execute(node.right, context)
                    if node.operator == BinaryOperator.ADD:
                        return left + right
                    elif node.operator == BinaryOperator.MULTIPLY:
                        return left * right
                    elif node.operator == BinaryOperator.PIPE:
                        # For testing, just return the right value
                        return right
                return node

        return StatementExecutor(MockParentExecutor(), FunctionRegistry())

    @pytest.fixture
    def context(self):
        """Create a sandbox context for testing."""
        return SandboxContext()

    def test_basic_declarative_function(self, executor, context):
        """Test basic declarative function execution."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("add_one"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
        )

        result = executor.execute_declarative_function_definition(node, context)
        assert result is not None
        assert callable(result)
        assert result.__name__ == "add_one"

        # Test calling the function
        func_result = result(5)
        assert func_result == 6

    def test_declarative_function_without_parameters(self, executor, context):
        """Test declarative function without parameters."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("get_constant"), parameters=[], return_type=TypeHint("int"), composition=LiteralExpression(42)
        )

        result = executor.execute_declarative_function_definition(node, context)
        assert result is not None
        assert callable(result)
        assert result.__name__ == "get_constant"

        # Test calling the function
        func_result = result()
        assert func_result == 42

    def test_declarative_function_with_multiple_parameters(self, executor, context):
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

        result = executor.execute_declarative_function_definition(node, context)
        assert result is not None
        assert callable(result)
        assert result.__name__ == "add_multiply"

        # Test calling the function
        func_result = result(2, 3, 4)
        assert func_result == 20  # (2 + 3) * 4 = 20

    def test_declarative_function_with_default_values(self, executor, context):
        """Test declarative function with default parameter values."""
        # Create a function with default values
        node = DeclarativeFunctionDefinition(
            name=Identifier("greet"),
            parameters=[
                Parameter("name", TypeHint("str")),
                Parameter("greeting", TypeHint("str"), default_value=LiteralExpression("Hello")),
            ],
            return_type=TypeHint("str"),
            composition=BinaryExpression(left=Identifier("greeting"), operator=BinaryOperator.ADD, right=Identifier("name")),
        )

        result = executor.execute_declarative_function_definition(node, context)
        assert result is not None
        assert callable(result)

        # Test with both arguments
        func_result = result("Alice", "Hi ")
        assert func_result == "Hi Alice"

        # Test with default value
        func_result = result("Bob")
        assert func_result == "HelloBob"

    def test_declarative_function_parameter_validation(self, executor, context):
        """Test that declarative functions validate their parameters correctly."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=TypeHint("str"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=LiteralExpression(1)),
        )

        result = executor.execute_declarative_function_definition(node, context)

        # Test with correct number of arguments
        func_result = result(5, "test")
        assert func_result == 6

        # Test with missing required arguments
        with pytest.raises(TypeError, match="Missing required argument 'x'"):
            result()

        # Test with too many arguments
        with pytest.raises(TypeError, match="Too many positional arguments"):
            result(1, "test", "extra")

        # Test with unexpected keyword arguments
        with pytest.raises(TypeError, match="Unexpected keyword argument 'invalid'"):
            result(1, "test", invalid="value")

    def test_declarative_function_keyword_arguments(self, executor, context):
        """Test declarative function with keyword arguments."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("calculate"),
            parameters=[
                Parameter("x", TypeHint("int")),
                Parameter("y", TypeHint("int")),
                Parameter("operation", TypeHint("str"), default_value=LiteralExpression("add")),
            ],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=Identifier("y")),
        )

        result = executor.execute_declarative_function_definition(node, context)

        # Test with positional arguments
        func_result = result(2, 3)
        assert func_result == 5

        # Test with keyword arguments
        func_result = result(x=4, y=5)
        assert func_result == 9

        # Test with mixed positional and keyword arguments
        func_result = result(1, operation="multiply", y=2)
        assert func_result == 3

    def test_declarative_function_composition_argument_passing(self, executor, context):
        """Test that all arguments are properly passed to the composed function."""

        # Create a mock function that returns its arguments as a tuple
        def mock_composed_func(*args, **kwargs):
            return (args, kwargs)

        # Create a new executor with the mock parent
        class MockParentExecutor(BaseExecutor):
            def __init__(self):
                super().__init__(parent=None)

            def execute(self, node, context):
                if isinstance(node, Identifier) and node.name == "mock_func":
                    return mock_composed_func
                elif isinstance(node, Identifier):
                    return context.get(f"local:{node.name}")
                elif isinstance(node, LiteralExpression):
                    return node.value
                elif isinstance(node, BinaryExpression):
                    left = self.execute(node.left, context)
                    right = self.execute(node.right, context)
                    if node.operator == BinaryOperator.ADD:
                        return left + right
                    elif node.operator == BinaryOperator.MULTIPLY:
                        return left * right
                    elif node.operator == BinaryOperator.PIPE:
                        return right
                return node

        # Create a new executor with the mock parent
        test_executor = StatementExecutor(MockParentExecutor(), FunctionRegistry())

        node = DeclarativeFunctionDefinition(
            name=Identifier("test_passing"),
            parameters=[
                Parameter("a", TypeHint("int")),
                Parameter("b", TypeHint("str")),
                Parameter("c", TypeHint("float"), default_value=LiteralExpression(1.5)),
            ],
            return_type=TypeHint("tuple"),
            composition=Identifier("mock_func"),
        )

        result = test_executor.execute_declarative_function_definition(node, context)

        # Test that positional arguments are passed correctly
        # Note: Only positional arguments are passed to the composed function
        # Keyword arguments are bound to the context but not passed as arguments
        args, kwargs = result(10, "test")
        assert args == (10, "test")  # Only the explicitly passed positional arguments
        assert kwargs == {}

        # Test with keyword arguments - these are bound to context but not passed as args
        args, kwargs = result(a=20, b="keyword")
        assert args == ()  # No positional arguments passed to composed function
        assert kwargs == {}

        # Test with all arguments explicitly provided as positional
        args, kwargs = result(10, "test", 2.5)
        assert args == (10, "test", 2.5)
        assert kwargs == {}

    def test_declarative_function_default_value_evaluation_error(self, executor, context):
        """Test handling of default value evaluation errors."""

        # Create a parameter with a default value that will fail to evaluate
        class FailingExpression:
            def __init__(self):
                pass

        node = DeclarativeFunctionDefinition(
            name=Identifier("test_default_error"),
            parameters=[
                Parameter("x", TypeHint("int")),
                Parameter("y", TypeHint("int"), default_value=FailingExpression()),
            ],
            return_type=TypeHint("int"),
            composition=BinaryExpression(left=Identifier("x"), operator=BinaryOperator.ADD, right=Identifier("y")),
        )

        result = executor.execute_declarative_function_definition(node, context)

        # The function should still be created, but calling it with missing y should fail
        # The error will occur during composition execution when trying to evaluate y
        with pytest.raises(TypeError, match="unsupported operand type"):
            result(5)

        # Should work with both arguments provided
        func_result = result(5, 3)
        assert func_result == 8
