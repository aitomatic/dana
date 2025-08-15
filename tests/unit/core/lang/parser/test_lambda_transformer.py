"""Unit tests for LambdaTransformer."""

from lark import Tree, Token
from dana.core.lang.ast import LambdaExpression, Parameter, TypeHint, LiteralExpression
from dana.core.lang.parser.transformer.expression.lambda_transformer import LambdaTransformer


class TestLambdaTransformer:
    """Test cases for LambdaTransformer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = LambdaTransformer()

    def test_lambda_receiver_transformation(self):
        """Test transformation of lambda receiver."""
        # Create mock tree for: (point: Point)
        items = [Token("NAME", "point"), Token("NAME", "Point")]
        result = self.transformer.lambda_receiver(items)

        assert isinstance(result, Tree)
        assert result.data == "lambda_receiver"
        assert len(result.children) == 2

    def test_lambda_params_transformation(self):
        """Test transformation of lambda parameters."""
        # Create mock tree for: x: int, y: float
        items = [Token("NAME", "x"), Token("NAME", "int"), Token("NAME", "y"), Token("NAME", "float")]
        result = self.transformer.lambda_params(items)

        assert isinstance(result, Tree)
        assert result.data == "lambda_params"
        assert len(result.children) == 4

    def test_transform_receiver_with_type(self):
        """Test _transform_receiver with type hint."""
        items = [Token("NAME", "shape"), Token("NAME", "Circle")]
        receiver = self.transformer._transform_receiver(items)

        assert isinstance(receiver, Parameter)
        assert receiver.name == "shape"
        assert receiver.type_hint is not None
        assert receiver.type_hint.name == "Circle"

    def test_transform_receiver_minimal(self):
        """Test _transform_receiver with minimal items."""
        items = [Token("NAME", "obj")]
        receiver = self.transformer._transform_receiver(items)

        assert receiver is None  # Should return None if not enough items

    def test_transform_parameters_with_types(self):
        """Test _transform_parameters with type hints."""
        items = [Token("NAME", "x"), Token("NAME", "int"), Token("NAME", "y"), Token("NAME", "float")]
        parameters = self.transformer._transform_parameters(items)

        assert len(parameters) == 2
        assert parameters[0].name == "x"
        assert parameters[0].type_hint.name == "int"
        assert parameters[1].name == "y"
        assert parameters[1].type_hint.name == "float"

    def test_transform_parameters_without_types(self):
        """Test _transform_parameters without type hints."""
        items = [Token("NAME", "a"), Token("NAME", "b")]
        parameters = self.transformer._transform_parameters(items)

        assert len(parameters) == 2
        assert parameters[0].name == "a"
        assert parameters[0].type_hint is None
        assert parameters[1].name == "b"
        assert parameters[1].type_hint is None

    def test_transform_type_from_token(self):
        """Test _transform_type with a simple token."""
        type_hint = self.transformer._transform_type(Token("NAME", "str"))

        assert isinstance(type_hint, TypeHint)
        assert type_hint.name == "str"

    def test_transform_type_from_tree(self):
        """Test _transform_type with a tree structure."""
        tree = Tree("basic_type", [Token("NAME", "list")])
        type_hint = self.transformer._transform_type(tree)

        assert isinstance(type_hint, TypeHint)
        assert type_hint.name == "list"

    def test_transform_type_fallback(self):
        """Test _transform_type fallback to 'any'."""
        type_hint = self.transformer._transform_type(None)

        assert isinstance(type_hint, TypeHint)
        assert type_hint.name == "any"

    def test_lambda_expr_with_body_only(self):
        """Test lambda_expr transformation with body only."""
        body = LiteralExpression(value=42)
        items = [body]

        result = self.transformer.lambda_expr(items)

        assert isinstance(result, LambdaExpression)
        assert result.receiver is None
        assert result.parameters == []
        assert result.body == body

    def test_lambda_expr_with_receiver_and_params(self):
        """Test lambda_expr transformation with receiver and parameters."""
        # Create mock trees
        receiver_tree = Tree("lambda_receiver", [Token("NAME", "point"), Token("NAME", "Point")])
        params_tree = Tree("lambda_params", [Token("NAME", "dx"), Token("NAME", "int")])
        body = LiteralExpression(value="result")

        items = [receiver_tree, params_tree, body]
        result = self.transformer.lambda_expr(items)

        assert isinstance(result, LambdaExpression)
        assert result.receiver is not None
        assert result.receiver.name == "point"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "dx"
        assert result.body == body

    def test_lambda_expr_with_params_only(self):
        """Test lambda_expr transformation with parameters only."""
        params_tree = Tree("lambda_params", [Token("NAME", "x"), Token("NAME", "y")])
        body = LiteralExpression(value="test")

        items = [params_tree, body]
        result = self.transformer.lambda_expr(items)

        assert isinstance(result, LambdaExpression)
        assert result.receiver is None
        assert len(result.parameters) == 2
        assert result.parameters[0].name == "x"
        assert result.parameters[1].name == "y"
        assert result.body == body
