"""Unit tests for LambdaExpression AST node."""

from dana.core.lang.ast import LambdaExpression, Parameter, TypeHint, LiteralExpression


class TestLambdaExpression:
    """Test cases for LambdaExpression AST node."""

    def test_lambda_expression_creation(self):
        """Test basic lambda expression creation."""
        body = LiteralExpression(value=42)
        lambda_expr = LambdaExpression(body=body)

        assert lambda_expr.receiver is None
        assert lambda_expr.parameters == []
        assert lambda_expr.body == body
        assert lambda_expr.location is None

    def test_lambda_expression_with_parameters(self):
        """Test lambda expression with parameters."""
        param1 = Parameter(name="x", type_hint=TypeHint(name="int"))
        param2 = Parameter(name="y", type_hint=TypeHint(name="int"))
        body = LiteralExpression(value="test")

        lambda_expr = LambdaExpression(parameters=[param1, param2], body=body)

        assert lambda_expr.receiver is None
        assert len(lambda_expr.parameters) == 2
        assert lambda_expr.parameters[0].name == "x"
        assert lambda_expr.parameters[1].name == "y"
        assert lambda_expr.body == body

    def test_lambda_expression_with_receiver(self):
        """Test lambda expression with struct receiver."""
        receiver = Parameter(name="point", type_hint=TypeHint(name="Point"))
        param = Parameter(name="dx", type_hint=TypeHint(name="int"))
        body = LiteralExpression(value="result")

        lambda_expr = LambdaExpression(receiver=receiver, parameters=[param], body=body)

        assert lambda_expr.receiver is not None
        assert lambda_expr.receiver.name == "point"
        assert lambda_expr.receiver.type_hint.name == "Point"
        assert len(lambda_expr.parameters) == 1
        assert lambda_expr.parameters[0].name == "dx"
        assert lambda_expr.body == body

    def test_lambda_expression_with_receiver_and_multiple_params(self):
        """Test lambda expression with receiver and multiple parameters."""
        receiver = Parameter(name="shape", type_hint=TypeHint(name="Shape"))
        param1 = Parameter(name="x", type_hint=TypeHint(name="float"))
        param2 = Parameter(name="y", type_hint=TypeHint(name="float"))
        body = LiteralExpression(value=0.0)

        lambda_expr = LambdaExpression(receiver=receiver, parameters=[param1, param2], body=body)

        assert lambda_expr.receiver.name == "shape"
        assert lambda_expr.receiver.type_hint.name == "Shape"
        assert len(lambda_expr.parameters) == 2
        assert lambda_expr.parameters[0].name == "x"
        assert lambda_expr.parameters[1].name == "y"
        assert lambda_expr.body == body

    def test_lambda_expression_empty_parameters(self):
        """Test lambda expression with no parameters."""
        body = LiteralExpression(value="no params")
        lambda_expr = LambdaExpression(body=body)

        assert lambda_expr.receiver is None
        assert lambda_expr.parameters == []
        assert lambda_expr.body == body

    def test_lambda_expression_parameters_without_types(self):
        """Test lambda expression with parameters that have no type hints."""
        param1 = Parameter(name="a")
        param2 = Parameter(name="b")
        body = LiteralExpression(value="untyped")

        lambda_expr = LambdaExpression(parameters=[param1, param2], body=body)

        assert len(lambda_expr.parameters) == 2
        assert lambda_expr.parameters[0].name == "a"
        assert lambda_expr.parameters[0].type_hint is None
        assert lambda_expr.parameters[1].name == "b"
        assert lambda_expr.parameters[1].type_hint is None
