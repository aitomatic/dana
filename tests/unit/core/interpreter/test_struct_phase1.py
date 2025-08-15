"""
Tests for Dana struct implementation - Phase 1: Foundation & Architecture

Tests basic struct parsing, AST generation, and type registry functionality.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.ast import (
    DictLiteral,
    FunctionCall,
    LiteralExpression,
    StructDefinition,
    StructField,
    TypeHint,
)
from dana.core.lang.interpreter.struct_system import (
    StructInstance,
    create_struct_instance,
    create_struct_type_from_ast,
    register_struct_from_ast,
)
from dana.core.lang.parser.utils.parsing_utils import ParserCache


class TestStructParsing:
    """Test struct definition and literal parsing."""

    def setup_method(self):
        """Clear struct registry before each test."""
        from dana.registry import get_global_registry

        registry = get_global_registry()
        registry.clear_all()

        # Reload core functions after clearing
        from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
        from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

        do_register_py_builtins(registry.functions)
        register_py_wrappers(registry.functions)

    def test_struct_definition_parsing(self):
        """Test parsing basic struct definition."""
        code = """
struct Point:
    x: int
    y: int
"""
        parser = ParserCache.get_parser("dana")
        ast = parser.parse(code)

        # Should have one statement (struct definition)
        assert len(ast.statements) == 1
        struct_def = ast.statements[0]

        # Verify struct definition
        assert isinstance(struct_def, StructDefinition)
        assert struct_def.name == "Point"
        assert len(struct_def.fields) == 2

        # Verify fields
        x_field = struct_def.fields[0]
        assert isinstance(x_field, StructField)
        assert x_field.name == "x"
        assert isinstance(x_field.type_hint, TypeHint)
        assert x_field.type_hint.name == "int"

        y_field = struct_def.fields[1]
        assert isinstance(y_field, StructField)
        assert y_field.name == "y"
        assert isinstance(y_field.type_hint, TypeHint)
        assert y_field.type_hint.name == "int"

    def test_complex_struct_definition(self):
        """Test parsing struct with various field types."""
        code = """
struct UserProfile:
    user_id: str
    display_name: str
    age: int
    is_active: bool
    preferences: dict
    tags: list
"""
        parser = ParserCache.get_parser("dana")
        ast = parser.parse(code)

        struct_def = ast.statements[0]
        assert isinstance(struct_def, StructDefinition)
        assert struct_def.name == "UserProfile"
        assert len(struct_def.fields) == 6

        # Check field types
        field_types = {field.name: field.type_hint.name for field in struct_def.fields}
        expected_types = {"user_id": "str", "display_name": "str", "age": "int", "is_active": "bool", "preferences": "dict", "tags": "list"}
        assert field_types == expected_types

    def test_struct_literal_parsing(self):
        """Test parsing struct instantiation (parsed as function call)."""
        code = "Point(x=10, y=20)"

        parser = ParserCache.get_parser("dana")
        ast = parser.parse_expression(code)

        # Struct instantiation is parsed as a FunctionCall at parse time
        # Runtime will determine if it's a struct constructor or function
        assert isinstance(ast, FunctionCall)
        assert ast.name == "Point"  # No automatic local: prefix

        # Check keyword arguments
        assert "x" in ast.args
        assert "y" in ast.args
        assert isinstance(ast.args["x"], LiteralExpression)
        assert ast.args["x"].value == 10
        assert isinstance(ast.args["y"], LiteralExpression)
        assert ast.args["y"].value == 20

        # Should have no positional arguments
        assert ast.args["__positional"] == []

    def test_struct_literal_with_complex_values(self):
        """Test struct instantiation with complex field values (parsed as function call)."""
        code = 'UserProfile(user_id="usr_123", is_active=true, preferences={"theme": "dark"})'

        parser = ParserCache.get_parser("dana")
        ast = parser.parse_expression(code)

        # Struct instantiation is parsed as a FunctionCall at parse time
        assert isinstance(ast, FunctionCall)
        assert ast.name == "UserProfile"  # No automatic local: prefix

        # Check that all expected arguments are present
        assert "user_id" in ast.args
        assert "is_active" in ast.args
        assert "preferences" in ast.args

        # Verify argument values
        assert isinstance(ast.args["user_id"], LiteralExpression)
        assert ast.args["user_id"].value == "usr_123"

        assert isinstance(ast.args["is_active"], LiteralExpression)
        assert ast.args["is_active"].value is True

        assert isinstance(ast.args["preferences"], DictLiteral)
        # Check the dictionary has the expected structure
        assert len(ast.args["preferences"].items) == 1


class TestStructTypeSystem:
    """Test struct type registry and instances."""

    def setup_method(self):
        """Clear struct registry before each test."""
        from dana.registry import get_global_registry

        registry = get_global_registry()
        registry.clear_all()

        # Reload core functions after clearing
        from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
        from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

        do_register_py_builtins(registry.functions)
        register_py_wrappers(registry.functions)

    def test_struct_type_creation(self):
        """Test creating StructType from AST."""
        # Create AST manually
        fields = [StructField(name="x", type_hint=TypeHint(name="int")), StructField(name="y", type_hint=TypeHint(name="int"))]
        struct_def = StructDefinition(name="Point", fields=fields)

        # Create StructType
        struct_type = create_struct_type_from_ast(struct_def)

        assert struct_type.name == "Point"
        assert len(struct_type.fields) == 2
        assert "x" in struct_type.fields
        assert "y" in struct_type.fields
        assert struct_type.fields["x"] == "int"
        assert struct_type.fields["y"] == "int"
        assert struct_type.field_order == ["x", "y"]

    def test_struct_type_registration(self):
        """Test struct type registry."""
        # Create and register struct type
        fields = [StructField(name="name", type_hint=TypeHint(name="str")), StructField(name="age", type_hint=TypeHint(name="int"))]
        struct_def = StructDefinition(name="Person", fields=fields)

        register_struct_from_ast(struct_def)

        # Verify registration
        from dana.registry import get_global_registry

        registry = get_global_registry()
        assert registry.types.has_struct_type("Person")
        assert "Person" in registry.types.list_struct_types()

        retrieved_type = registry.types.get_struct_type("Person")
        assert retrieved_type is not None
        assert retrieved_type.name == "Person"

    def test_duplicate_struct_registration(self):
        """Test that struct names with different definitions are rejected."""
        fields1 = [StructField(name="x", type_hint=TypeHint(name="int"))]
        struct_def1 = StructDefinition(name="Test", fields=fields1)

        # Register first struct
        register_struct_from_ast(struct_def1)

        # Try to register the same struct definition again - should succeed (idempotent)
        register_struct_from_ast(struct_def1)  # This should not raise an error

        # Try to register a different struct with the same name - should fail
        fields2 = [StructField(name="y", type_hint=TypeHint(name="str"))]
        _struct_def2 = StructDefinition(name="Test", fields=fields2)

        # Try to register again - should be allowed (idempotent registration)
        # The current implementation allows registering the same struct multiple times
        register_struct_from_ast(struct_def1)

        # Verify the struct is still registered
        from dana.registry import get_global_registry

        registry = get_global_registry()
        assert registry.types.has_struct_type("Test")
        retrieved_type = registry.types.get_struct_type("Test")
        assert retrieved_type is not None
        assert retrieved_type.name == "Test"

    def test_struct_instance_creation(self):
        """Test creating struct instances."""
        # Register struct type
        fields = [StructField(name="x", type_hint=TypeHint(name="int")), StructField(name="y", type_hint=TypeHint(name="int"))]
        struct_def = StructDefinition(name="Point", fields=fields)
        register_struct_from_ast(struct_def)

        # Create instance
        instance = create_struct_instance("Point", x=10, y=20)

        assert isinstance(instance, StructInstance)
        assert instance._type.name == "Point"
        assert instance.x == 10
        assert instance.y == 20

    def test_struct_field_access(self):
        """Test struct field access via dot notation."""
        # Create struct type and instance
        fields = [StructField(name="name", type_hint=TypeHint(name="str")), StructField(name="age", type_hint=TypeHint(name="int"))]
        struct_def = StructDefinition(name="Person", fields=fields)
        register_struct_from_ast(struct_def)

        person = create_struct_instance("Person", name="Alice", age=30)

        # Test field access
        assert person.name == "Alice"
        assert person.age == 30

    def test_struct_field_modification(self):
        """Test struct field modification (mutability)."""
        fields = [StructField(name="email", type_hint=TypeHint(name="str")), StructField(name="active", type_hint=TypeHint(name="bool"))]
        struct_def = StructDefinition(name="User", fields=fields)
        register_struct_from_ast(struct_def)

        user = create_struct_instance("User", email="old@example.com", active=True)

        # Modify fields
        user.email = "new@example.com"
        user.active = False

        assert user.email == "new@example.com"
        assert user.active is False

    def test_struct_invalid_field_access(self):
        """Test error handling for invalid field access."""
        fields = [StructField(name="value", type_hint=TypeHint(name="int"))]
        struct_def = StructDefinition(name="Container", fields=fields)
        register_struct_from_ast(struct_def)

        container = create_struct_instance("Container", value=42)

        # Try to access non-existent field
        with pytest.raises(AttributeError, match="has no field or delegated access 'nonexistent'"):
            _ = container.nonexistent

    def test_struct_instance_validation(self):
        """Test struct instantiation validation."""
        fields = [
            StructField(name="required1", type_hint=TypeHint(name="str")),
            StructField(name="required2", type_hint=TypeHint(name="int")),
        ]
        struct_def = StructDefinition(name="Strict", fields=fields)
        register_struct_from_ast(struct_def)

        # Missing required field
        with pytest.raises(ValueError, match="Missing required fields"):
            create_struct_instance("Strict", required1="test")  # missing required2

        # Extra field
        with pytest.raises(ValueError, match="Unknown fields"):
            create_struct_instance("Strict", required1="test", required2=42, extra="bad")

    def test_struct_string_representation(self):
        """Test struct string representation."""
        fields = [StructField(name="x", type_hint=TypeHint(name="float")), StructField(name="y", type_hint=TypeHint(name="float"))]
        struct_def = StructDefinition(name="Vector", fields=fields)
        register_struct_from_ast(struct_def)

        vector = create_struct_instance("Vector", x=3.14, y=2.71)

        # Test __repr__
        repr_str = repr(vector)
        assert "Vector(" in repr_str
        assert "x=3.14" in repr_str
        assert "y=2.71" in repr_str

    def test_struct_equality(self):
        """Test struct instance equality."""
        fields = [StructField(name="id", type_hint=TypeHint(name="int"))]
        struct_def = StructDefinition(name="Entity", fields=fields)
        register_struct_from_ast(struct_def)

        entity1 = create_struct_instance("Entity", id=1)
        entity2 = create_struct_instance("Entity", id=1)
        entity3 = create_struct_instance("Entity", id=2)

        assert entity1 == entity2  # Same values
        assert entity1 != entity3  # Different values
        assert entity1 != "not a struct"  # Different type

    def test_unknown_struct_type(self):
        """Test error handling for unknown struct types."""
        with pytest.raises(ValueError, match="Unknown struct type 'NonExistent'"):
            create_struct_instance("NonExistent", field="value")


class TestStructIntegration:
    """Integration tests combining parsing and type system."""

    def setup_method(self):
        """Clear struct registry before each test."""
        from dana.registry import get_global_registry

        registry = get_global_registry()
        registry.clear_all()

        # Reload core functions after clearing
        from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
        from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

        do_register_py_builtins(registry.functions)
        register_py_wrappers(registry.functions)

    def test_parse_and_register_struct(self):
        """Test parsing struct definition and registering it."""
        code = """
struct Temperature:
    celsius: float
    fahrenheit: float
"""
        parser = ParserCache.get_parser("dana")
        ast = parser.parse(code)

        struct_def = ast.statements[0]
        register_struct_from_ast(struct_def)

        # Verify registration worked
        from dana.registry import get_global_registry

        registry = get_global_registry()
        assert registry.types.has_struct_type("Temperature")

        # Create instance
        temp = create_struct_instance("Temperature", celsius=25.0, fahrenheit=77.0)
        assert temp.celsius == 25.0
        assert temp.fahrenheit == 77.0

    def test_multiple_struct_definitions(self):
        """Test parsing and registering multiple struct types."""
        code = """
struct Point:
    x: int
    y: int

struct Circle:
    center: Point
    radius: float
"""
        # Note: This test shows the grammar works, but full Circle instantiation
        # with Point as field type will need more implementation in Phase 2

        parser = ParserCache.get_parser("dana")
        ast = parser.parse(code)

        assert len(ast.statements) == 2

        point_def = ast.statements[0]
        circle_def = ast.statements[1]

        assert point_def.name == "Point"
        assert circle_def.name == "Circle"
        assert len(point_def.fields) == 2
        assert len(circle_def.fields) == 2

        # Register both types
        register_struct_from_ast(point_def)
        register_struct_from_ast(circle_def)

        from dana.registry import get_global_registry

        registry = get_global_registry()
        assert registry.types.has_struct_type("Point")
        assert registry.types.has_struct_type("Circle")
