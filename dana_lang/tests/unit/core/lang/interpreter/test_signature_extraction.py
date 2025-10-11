"""Unit tests for signature extraction in declarative functions."""

import inspect
from unittest.mock import Mock

from dana.core.lang.ast import (
    DeclarativeFunctionDefinition,
    Identifier,
    LiteralExpression,
    Parameter,
    TypeHint,
)
from dana.core.lang.interpreter.executor.statement_executor import StatementExecutor
from dana.core.lang.sandbox_context import SandboxContext


class TestSignatureExtraction:
    """Test signature extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_parent = Mock()
        self.mock_parent.execute = Mock(return_value=42)

        self.executor = StatementExecutor(self.mock_parent)
        self.context = SandboxContext()

    def test_extract_annotations_basic(self):
        """Test basic annotation extraction."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=TypeHint("bool"),
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check annotations
        expected_annotations = {"x": int, "y": str, "return": bool}
        assert result.__annotations__ == expected_annotations

    def test_extract_annotations_without_return_type(self):
        """Test annotation extraction without return type."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=None,
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check annotations (no return type)
        expected_annotations = {"x": int, "y": str}
        assert result.__annotations__ == expected_annotations

    def test_extract_annotations_without_type_hints(self):
        """Test annotation extraction without type hints."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[
                Parameter("x"),  # No type hint
                Parameter("y"),  # No type hint
            ],
            return_type=None,
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check annotations (should default to object)
        expected_annotations = {"x": object, "y": object}
        assert result.__annotations__ == expected_annotations

    def test_extract_annotations_complex_types(self):
        """Test annotation extraction with complex types."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[
                Parameter("data", TypeHint("list")),
                Parameter("config", TypeHint("dict")),
                Parameter("items", TypeHint("tuple")),
                Parameter("flags", TypeHint("set")),
            ],
            return_type=TypeHint("str"),
            composition=LiteralExpression("result"),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check annotations
        expected_annotations = {"data": list, "config": dict, "items": tuple, "flags": set, "return": str}
        assert result.__annotations__ == expected_annotations

    def test_create_signature_basic(self):
        """Test basic signature creation."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=TypeHint("bool"),
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check signature
        assert hasattr(result, "__signature__")
        signature = result.__signature__
        assert isinstance(signature, inspect.Signature)

        # Check parameters
        params = list(signature.parameters.values())
        assert len(params) == 2
        assert params[0].name == "x"
        assert params[0].annotation == int
        assert params[1].name == "y"
        assert params[1].annotation == str

        # Check return annotation
        assert signature.return_annotation == bool

    def test_create_signature_without_return_type(self):
        """Test signature creation without return type."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=None,
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check signature
        signature = result.__signature__
        assert signature.return_annotation == object  # Default to object

    def test_create_signature_without_parameters(self):
        """Test signature creation without parameters."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"), parameters=[], return_type=TypeHint("int"), composition=LiteralExpression(42)
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check signature
        signature = result.__signature__
        assert len(signature.parameters) == 0
        assert signature.return_annotation == int

    def test_create_signature_parameter_kinds(self):
        """Test that parameters are created with correct kinds."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=TypeHint("bool"),
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check parameter kinds
        signature = result.__signature__
        params = list(signature.parameters.values())

        for param in params:
            assert param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    def test_map_dana_type_to_python(self):
        """Test Dana type to Python type mapping."""
        # Test basic types
        assert self.executor._map_dana_type_to_python("int") == int
        assert self.executor._map_dana_type_to_python("str") == str
        assert self.executor._map_dana_type_to_python("bool") == bool
        assert self.executor._map_dana_type_to_python("float") == float
        assert self.executor._map_dana_type_to_python("list") == list
        assert self.executor._map_dana_type_to_python("dict") == dict
        assert self.executor._map_dana_type_to_python("tuple") == tuple
        assert self.executor._map_dana_type_to_python("set") == set

        # Test special types
        assert self.executor._map_dana_type_to_python("None") == type(None)
        assert self.executor._map_dana_type_to_python("any") == object
        assert self.executor._map_dana_type_to_python("Any") == object

        # Test unknown types
        assert self.executor._map_dana_type_to_python("unknown_type") == object

    def test_signature_inspection_works(self):
        """Test that signature inspection works correctly."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int")), Parameter("y", TypeHint("str"))],
            return_type=TypeHint("bool"),
            composition=LiteralExpression(True),
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Test inspect.signature() works
        signature = inspect.signature(result)
        assert len(signature.parameters) == 2
        assert "x" in signature.parameters
        assert "y" in signature.parameters
        assert signature.parameters["x"].annotation == int
        assert signature.parameters["y"].annotation == str
        assert signature.return_annotation == bool

    def test_function_metadata_completeness(self):
        """Test that all function metadata is properly set."""
        node = DeclarativeFunctionDefinition(
            name=Identifier("test_func"),
            parameters=[Parameter("x", TypeHint("int"))],
            return_type=TypeHint("str"),
            composition=LiteralExpression("test"),
            docstring="Test function documentation",
        )

        result = self.executor.execute_declarative_function_definition(node, self.context)

        # Check all metadata
        assert result.__name__ == "test_func"
        assert result.__qualname__ == "test_func"
        assert result.__doc__ == "Test function documentation"
        assert result.__annotations__ == {"x": int, "return": str}
        assert hasattr(result, "__signature__")
        assert isinstance(result.__signature__, inspect.Signature)
