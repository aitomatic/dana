"""
Unit tests for parsing declarative function definitions.

Tests the parser's ability to parse the new declarative function definition syntax.
"""

from dana.core.lang.ast import (
    DeclarativeFunctionDefinition,
    PipelineExpression,
)
from dana.core.lang.parser import DanaParser


class TestDeclarativeFunctionDefinitionParsing:
    """Test cases for parsing declarative function definitions."""

    def setup_method(self):
        """Set up parser for each test."""
        self.parser = DanaParser()

    def test_parse_basic_declarative_function(self):
        """Test parsing a basic declarative function definition."""
        # Arrange
        source = "def simple_func(x: int) -> str = f1 | f2"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "simple_func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "x"
        assert statement.parameters[0].type_hint.name == "int"
        assert statement.return_type.name == "str"
        assert isinstance(statement.composition, PipelineExpression)
        assert len(statement.composition.stages) == 2
        assert statement.composition.stages[0].name == "f1"
        assert statement.composition.stages[1].name == "f2"

    def test_parse_declarative_function_without_return_type(self):
        """Test parsing a declarative function without return type."""
        # Arrange
        source = "def func(x: int) = f1 | f2"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "func"
        assert statement.return_type is None

    def test_parse_declarative_function_without_parameters(self):
        """Test parsing a declarative function without parameters."""
        # Arrange
        source = "def func() -> str = f1"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "func"
        assert len(statement.parameters) == 0
        assert statement.return_type.name == "str"

    def test_parse_declarative_function_with_multiple_parameters(self):
        """Test parsing a declarative function with multiple parameters."""
        # Arrange
        source = "def complex_func(x: int, y: float, z: str) -> dict = f1 | f2 | f3"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "complex_func"
        assert len(statement.parameters) == 3
        assert statement.parameters[0].name == "x"
        assert statement.parameters[0].type_hint.name == "int"
        assert statement.parameters[1].name == "y"
        assert statement.parameters[1].type_hint.name == "float"
        assert statement.parameters[2].name == "z"
        assert statement.parameters[2].type_hint.name == "str"

    def test_parse_declarative_function_with_parameters_without_type_hints(self):
        """Test parsing a declarative function with parameters without type hints."""
        # Arrange
        source = "def untyped_func(x, y) = f1"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "untyped_func"
        assert len(statement.parameters) == 2
        assert statement.parameters[0].name == "x"
        assert statement.parameters[0].type_hint is None
        assert statement.parameters[1].name == "y"
        assert statement.parameters[1].type_hint is None

    def test_parse_declarative_function_with_complex_composition(self):
        """Test parsing a declarative function with complex pipe composition."""
        # Arrange
        source = "def pipeline_func(data: dict) -> list = f1 | f2 | [f3, f4]"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "pipeline_func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "data"
        assert statement.parameters[0].type_hint.name == "dict"
        assert statement.return_type.name == "list"

    def test_parse_declarative_function_with_function_calls(self):
        """Test parsing a declarative function with function calls in composition."""
        # Arrange
        source = "def process_func(x: int) -> str = add_ten(x) | multiply(2) | stringify"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "process_func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "x"
        assert statement.parameters[0].type_hint.name == "int"
        assert statement.return_type.name == "str"

    def test_parse_declarative_function_with_nested_expressions(self):
        """Test parsing a declarative function with nested expressions."""
        # Arrange
        source = "def nested_func(x: int) -> float = (add_ten | multiply(2)) | divide(3)"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "nested_func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "x"
        assert statement.parameters[0].type_hint.name == "int"
        assert statement.return_type.name == "float"

    def test_parse_declarative_function_with_union_types(self):
        """Test parsing a declarative function with union types."""
        # Arrange
        source = "def union_func(x: int | float) -> str | None = f1 | f2"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "union_func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "x"
        # Note: Union type parsing would need to be implemented in the transformer
        assert statement.return_type is not None

    def test_parse_declarative_function_with_generic_types(self):
        """Test parsing a declarative function with generic types."""
        # Arrange
        source = "def generic_func(x: list[int]) -> dict[str, float] = f1 | f2"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "generic_func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "x"
        # Note: Generic type parsing would need to be implemented in the transformer
        assert statement.return_type is not None

    def test_parse_multiple_declarative_functions(self):
        """Test parsing multiple declarative function definitions."""
        # Arrange
        source = """
def func1(x: int) -> str = f1 | f2
def func2(y: float) -> int = f3 | f4
"""

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 2
        assert isinstance(result.statements[0], DeclarativeFunctionDefinition)
        assert isinstance(result.statements[1], DeclarativeFunctionDefinition)
        assert result.statements[0].name.name == "func1"
        assert result.statements[1].name.name == "func2"

    def test_parse_declarative_function_with_comments(self):
        """Test parsing a declarative function with comments."""
        # Arrange
        source = "def func(x: int) -> str = f1 | f2  # This is a comment"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "func"

    def test_parse_declarative_function_with_whitespace(self):
        """Test parsing a declarative function with various whitespace patterns."""
        # Arrange
        source = "def func ( x : int ) -> str = f1 | f2"

        # Act
        result = self.parser.parse(source)

        # Assert
        assert len(result.statements) == 1
        statement = result.statements[0]
        assert isinstance(statement, DeclarativeFunctionDefinition)
        assert statement.name.name == "func"
        assert len(statement.parameters) == 1
        assert statement.parameters[0].name == "x"
        assert statement.parameters[0].type_hint.name == "int"
        assert statement.return_type.name == "str"
