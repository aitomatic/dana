"""
Unit tests for DeclarativeFunctionDefinition AST node.

Tests the creation, validation, and basic functionality of declarative function definitions.
"""

from dana.core.lang.ast import (
    BinaryExpression,
    BinaryOperator,
    DeclarativeFunctionDefinition,
    Identifier,
    LiteralExpression,
    Location,
    Parameter,
    TypeHint,
)


class TestDeclarativeFunctionDefinition:
    """Test cases for DeclarativeFunctionDefinition AST node."""

    def test_basic_creation(self):
        """Test basic creation of DeclarativeFunctionDefinition."""
        # Arrange
        name = Identifier("test_func")
        parameters = [Parameter("x", TypeHint("int"))]
        return_type = TypeHint("str")
        composition = BinaryExpression(left=LiteralExpression("f1"), operator=BinaryOperator.PIPE, right=LiteralExpression("f2"))
        docstring = "Test function documentation"
        location = Location(line=1, column=1, source="test")

        # Act
        node = DeclarativeFunctionDefinition(
            name=name, parameters=parameters, return_type=return_type, composition=composition, docstring=docstring, location=location
        )

        # Assert
        assert node.name.name == "test_func"
        assert len(node.parameters) == 1
        assert node.parameters[0].name == "x"
        assert node.parameters[0].type_hint.name == "int"
        assert node.return_type.name == "str"
        assert isinstance(node.composition, BinaryExpression)
        assert node.composition.operator == BinaryOperator.PIPE
        assert node.docstring == "Test function documentation"
        assert node.location == location

    def test_creation_without_optional_fields(self):
        """Test creation without optional fields."""
        # Arrange
        name = Identifier("simple_func")
        parameters = []
        composition = LiteralExpression("f1")

        # Act
        node = DeclarativeFunctionDefinition(name=name, parameters=parameters, composition=composition)

        # Assert
        assert node.name.name == "simple_func"
        assert len(node.parameters) == 0
        assert node.return_type is None
        assert node.docstring is None
        assert node.location is None

    def test_creation_with_multiple_parameters(self):
        """Test creation with multiple parameters."""
        # Arrange
        name = Identifier("complex_func")
        parameters = [Parameter("x", TypeHint("int")), Parameter("y", TypeHint("float")), Parameter("z", TypeHint("str"))]
        composition = LiteralExpression("f1")

        # Act
        node = DeclarativeFunctionDefinition(name=name, parameters=parameters, composition=composition)

        # Assert
        assert len(node.parameters) == 3
        assert node.parameters[0].name == "x"
        assert node.parameters[0].type_hint.name == "int"
        assert node.parameters[1].name == "y"
        assert node.parameters[1].type_hint.name == "float"
        assert node.parameters[2].name == "z"
        assert node.parameters[2].type_hint.name == "str"

    def test_creation_with_parameters_without_type_hints(self):
        """Test creation with parameters that don't have type hints."""
        # Arrange
        name = Identifier("untyped_func")
        parameters = [
            Parameter("x"),  # No type hint
            Parameter("y"),  # No type hint
        ]
        composition = LiteralExpression("f1")

        # Act
        node = DeclarativeFunctionDefinition(name=name, parameters=parameters, composition=composition)

        # Assert
        assert len(node.parameters) == 2
        assert node.parameters[0].name == "x"
        assert node.parameters[0].type_hint is None
        assert node.parameters[1].name == "y"
        assert node.parameters[1].type_hint is None

    def test_creation_with_complex_composition(self):
        """Test creation with complex pipe composition."""
        # Arrange
        name = Identifier("pipeline_func")
        parameters = [Parameter("data", TypeHint("dict"))]

        # Create a complex composition: f1 | f2 | [f3, f4]
        f1 = LiteralExpression("f1")
        f2 = LiteralExpression("f2")
        f3 = LiteralExpression("f3")
        f4 = LiteralExpression("f4")

        # f1 | f2
        step1 = BinaryExpression(left=f1, operator=BinaryOperator.PIPE, right=f2)

        # [f3, f4] - This would be a ListLiteral in practice
        parallel = LiteralExpression([f3, f4])

        # (f1 | f2) | [f3, f4]
        composition = BinaryExpression(left=step1, operator=BinaryOperator.PIPE, right=parallel)

        # Act
        node = DeclarativeFunctionDefinition(name=name, parameters=parameters, composition=composition)

        # Assert
        assert node.name.name == "pipeline_func"
        assert len(node.parameters) == 1
        assert isinstance(node.composition, BinaryExpression)
        assert node.composition.operator == BinaryOperator.PIPE

    def test_equality_comparison(self):
        """Test equality comparison between DeclarativeFunctionDefinition nodes."""
        # Arrange
        node1 = DeclarativeFunctionDefinition(
            name=Identifier("func"), parameters=[Parameter("x", TypeHint("int"))], composition=LiteralExpression("f1")
        )

        node2 = DeclarativeFunctionDefinition(
            name=Identifier("func"), parameters=[Parameter("x", TypeHint("int"))], composition=LiteralExpression("f1")
        )

        node3 = DeclarativeFunctionDefinition(
            name=Identifier("different_func"), parameters=[Parameter("x", TypeHint("int"))], composition=LiteralExpression("f1")
        )

        # Assert
        assert node1 == node2
        assert node1 != node3

    def test_string_representation(self):
        """Test string representation of DeclarativeFunctionDefinition."""
        # Arrange
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("str"),
            composition=BinaryExpression(left=LiteralExpression("f1"), operator=BinaryOperator.PIPE, right=LiteralExpression("f2")),
            docstring="Test function",
        )

        # Act
        result = str(node)

        # Assert
        assert "DeclarativeFunctionDefinition" in result
        assert "test_func" in result
        assert "x" in result
        assert "int" in result
        assert "str" in result

    def test_parameter_access_by_name(self):
        """Test accessing parameters by name."""
        # Arrange
        node = DeclarativeFunctionDefinition(
            name=Identifier("func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("float")), Parameter("z", TypeHint("str"))],
            composition=LiteralExpression("f1"),
        )

        # Act & Assert
        x_param = next((p for p in node.parameters if p.name == "x"), None)
        y_param = next((p for p in node.parameters if p.name == "y"), None)
        z_param = next((p for p in node.parameters if p.name == "z"), None)
        missing_param = next((p for p in node.parameters if p.name == "missing"), None)

        assert x_param is not None
        assert x_param.type_hint.name == "int"
        assert y_param is not None
        assert y_param.type_hint.name == "float"
        assert z_param is not None
        assert z_param.type_hint.name == "str"
        assert missing_param is None
