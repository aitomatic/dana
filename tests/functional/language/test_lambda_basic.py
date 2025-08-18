"""Basic functional tests for lambda expressions."""

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


class TestLambdaBasic:
    """Basic functional tests for lambda expressions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

    def test_simple_lambda_no_params(self):
        """Test a simple lambda expression with no parameters."""
        code = "lambda :: 42"
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be a callable function
        assert callable(result)

        # Calling the lambda should return the value
        assert result() == 42

    def test_simple_lambda_with_param(self):
        """Test a simple lambda expression with one parameter."""
        code = "lambda x :: x * 2"
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be a callable function
        assert callable(result)

        # Calling the lambda should work
        assert result(5) == 10
        assert result(3) == 6

    def test_lambda_with_multiple_params(self):
        """Test lambda expression with multiple parameters."""
        code = "lambda x, y :: x + y"
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be a callable function
        assert callable(result)

        # Calling the lambda should work
        assert result(3, 4) == 7
        assert result(10, 20) == 30

    def test_lambda_with_typed_params(self):
        """Test lambda expression with typed parameters."""
        code = "lambda x: int, y: int :: x * y"
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be a callable function
        assert callable(result)

        # Calling the lambda should work
        assert result(4, 5) == 20
        assert result(2, 3) == 6

    def test_lambda_complex_body(self):
        """Test lambda expression with complex body expression."""
        code = "lambda x :: x * x + 1"
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be a callable function
        assert callable(result)

        # Calling the lambda should work
        assert result(3) == 10  # 3 * 3 + 1 = 10
        assert result(5) == 26  # 5 * 5 + 1 = 26

    def test_lambda_nested_expressions(self):
        """Test lambda expression with nested arithmetic."""
        code = "lambda a, b :: (a + b) * (a - b)"
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be a callable function
        assert callable(result)

        # Calling the lambda should work
        assert result(5, 3) == 16  # (5 + 3) * (5 - 3) = 8 * 2 = 16
        assert result(10, 4) == 84  # (10 + 4) * (10 - 4) = 14 * 6 = 84

    def test_lambda_assignment_and_call(self):
        """Test assigning lambda to variable and calling it."""
        code = """
f = lambda x :: x * 3
result = f(7)
"""
        result = self.interpreter._eval_source_code(code, self.context)

        # The result should be the final assignment result
        assert result == 21  # 7 * 3 = 21

        # The lambda should also be stored in context
        f = self.context.get("f")
        assert callable(f)
        assert f(4) == 12  # 4 * 3 = 12

    def test_lambda_metadata(self):
        """Test that lambda functions store metadata correctly."""
        code = "lambda x: int, y: str :: x + 1"
        result = self.interpreter._eval_source_code(code, self.context)

        # Check lambda metadata
        assert hasattr(result, "_dana_lambda")
        assert result._dana_lambda is True
        assert hasattr(result, "_dana_parameters")
        assert len(result._dana_parameters) == 2
        assert result._dana_parameters[0].name == "x"
        assert result._dana_parameters[1].name == "y"

    def test_lambda_no_receiver_metadata(self):
        """Test that lambda without receiver has correct metadata."""
        code = "lambda x :: x"
        result = self.interpreter._eval_source_code(code, self.context)

        # Check receiver metadata
        assert hasattr(result, "_dana_receiver")
        assert result._dana_receiver is None
