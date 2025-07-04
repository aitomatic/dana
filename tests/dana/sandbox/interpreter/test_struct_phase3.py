"""
Tests for Phase 3: Struct error handling and edge cases.

This module tests comprehensive error detection, type validation, and edge case
handling for the Dana struct implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox, ExecutionResult
from dana.core.lang.interpreter.struct_system import (
    StructInstance,
    StructTypeRegistry,
    create_struct_instance,
    register_struct_from_ast,
)
from dana.core.lang.parser.ast import (
    StructDefinition,
    StructField,
    TypeHint,
)


class TestStructTypeValidation:
    """Test type validation during struct instantiation and field assignment."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()

    def test_type_validation_during_instantiation(self):
        """Test that struct instantiation validates field types."""
        # Create struct with typed fields
        fields = [
            StructField(name="name", type_hint=TypeHint(name="str")),
            StructField(name="age", type_hint=TypeHint(name="int")),
            StructField(name="active", type_hint=TypeHint(name="bool")),
        ]
        struct_def = StructDefinition(name="User", fields=fields)
        register_struct_from_ast(struct_def)

        # Valid instantiation should work
        user = create_struct_instance("User", name="Alice", age=30, active=True)
        assert user.name == "Alice"
        assert user.age == 30
        assert user.active is True

        # Invalid type for string field
        with pytest.raises(ValueError, match="Type validation failed.*name.*expected str.*got int"):
            create_struct_instance("User", name=123, age=30, active=True)

        # Invalid type for int field
        with pytest.raises(ValueError, match="Type validation failed.*age.*expected int.*got str"):
            create_struct_instance("User", name="Alice", age="thirty", active=True)

        # Invalid type for bool field
        with pytest.raises(ValueError, match="Type validation failed.*active.*expected bool.*got str"):
            create_struct_instance("User", name="Alice", age=30, active="yes")

    def test_type_validation_during_field_assignment(self):
        """Test that field assignment validates types."""
        fields = [StructField(name="x", type_hint=TypeHint(name="int")), StructField(name="label", type_hint=TypeHint(name="str"))]
        struct_def = StructDefinition(name="Point", fields=fields)
        register_struct_from_ast(struct_def)

        point = create_struct_instance("Point", x=10, label="origin")

        # Valid assignments should work
        point.x = 20
        point.label = "new_point"
        assert point.x == 20
        assert point.label == "new_point"

        # Invalid type assignments should fail
        with pytest.raises(TypeError, match="Field assignment failed.*x.*expected int.*got str"):
            point.x = "not_a_number"

        with pytest.raises(TypeError, match="Field assignment failed.*label.*expected str.*got int"):
            point.label = 42

    def test_none_value_handling(self):
        """Test handling of None/null values."""
        fields = [
            StructField(name="optional_data", type_hint=TypeHint(name="any")),
            StructField(name="required_str", type_hint=TypeHint(name="str")),
        ]
        struct_def = StructDefinition(name="Container", fields=fields)
        register_struct_from_ast(struct_def)

        # None should be accepted for 'any' type
        container = create_struct_instance("Container", optional_data=None, required_str="test")
        assert container.optional_data is None

        # None should be rejected for specific types
        with pytest.raises(ValueError, match="Type validation failed.*required_str.*expected str.*got NoneType"):
            create_struct_instance("Container", optional_data="data", required_str=None)

    def test_list_and_dict_type_validation(self):
        """Test validation of list and dict types."""
        fields = [StructField(name="tags", type_hint=TypeHint(name="list")), StructField(name="metadata", type_hint=TypeHint(name="dict"))]
        struct_def = StructDefinition(name="Document", fields=fields)
        register_struct_from_ast(struct_def)

        # Valid types should work
        doc = create_struct_instance("Document", tags=["tag1", "tag2"], metadata={"key": "value"})
        assert doc.tags == ["tag1", "tag2"]
        assert doc.metadata == {"key": "value"}

        # Invalid types should fail
        with pytest.raises(ValueError, match="Type validation failed.*tags.*expected list.*got str"):
            create_struct_instance("Document", tags="not_a_list", metadata={})

        with pytest.raises(ValueError, match="Type validation failed.*metadata.*expected dict.*got list"):
            create_struct_instance("Document", tags=[], metadata=["not", "a", "dict"])

    def test_nested_struct_type_validation(self):
        """Test validation of nested struct types."""
        # Create Point struct
        point_fields = [StructField(name="x", type_hint=TypeHint(name="int")), StructField(name="y", type_hint=TypeHint(name="int"))]
        point_def = StructDefinition(name="Point", fields=point_fields)
        register_struct_from_ast(point_def)

        # Create Circle struct with Point field
        circle_fields = [
            StructField(name="center", type_hint=TypeHint(name="Point")),
            StructField(name="radius", type_hint=TypeHint(name="float")),
        ]
        circle_def = StructDefinition(name="Circle", fields=circle_fields)
        register_struct_from_ast(circle_def)

        # Valid nested struct should work
        center_point = create_struct_instance("Point", x=0, y=0)
        circle = create_struct_instance("Circle", center=center_point, radius=5.0)
        assert isinstance(circle.center, StructInstance)
        assert circle.center.x == 0

        # Invalid nested struct type should fail
        with pytest.raises(ValueError, match="Type validation failed.*center.*expected Point"):
            create_struct_instance("Circle", center="not_a_point", radius=5.0)


class TestStructErrorMessages:
    """Test comprehensive error messages and suggestions."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()

    def test_missing_fields_error_message(self):
        """Test clear error messages for missing fields."""
        fields = [
            StructField(name="required1", type_hint=TypeHint(name="str")),
            StructField(name="required2", type_hint=TypeHint(name="int")),
        ]
        struct_def = StructDefinition(name="TestStruct", fields=fields)
        register_struct_from_ast(struct_def)

        # Missing one field
        with pytest.raises(ValueError) as exc_info:
            create_struct_instance("TestStruct", required1="test")

        error_msg = str(exc_info.value)
        assert "Missing required fields for struct 'TestStruct'" in error_msg
        assert "required2" in error_msg
        assert "Required fields: ['required1', 'required2']" in error_msg

    def test_extra_fields_error_message(self):
        """Test clear error messages for extra fields."""
        fields = [StructField(name="valid_field", type_hint=TypeHint(name="str"))]
        struct_def = StructDefinition(name="TestStruct", fields=fields)
        register_struct_from_ast(struct_def)

        with pytest.raises(ValueError) as exc_info:
            create_struct_instance("TestStruct", valid_field="test", extra_field="bad")

        error_msg = str(exc_info.value)
        assert "Unknown fields for struct 'TestStruct'" in error_msg
        assert "extra_field" in error_msg
        assert "Valid fields: ['valid_field']" in error_msg

    def test_type_error_comprehensive_message(self):
        """Test that type errors include comprehensive information."""
        fields = [StructField(name="number", type_hint=TypeHint(name="int")), StructField(name="text", type_hint=TypeHint(name="str"))]
        struct_def = StructDefinition(name="TestStruct", fields=fields)
        register_struct_from_ast(struct_def)

        # Multiple type errors in one instantiation
        with pytest.raises(ValueError) as exc_info:
            create_struct_instance("TestStruct", number="not_int", text=123)

        error_msg = str(exc_info.value)
        assert "Type validation failed for struct 'TestStruct'" in error_msg
        assert "number" in error_msg
        assert "expected int" in error_msg
        assert "got str" in error_msg
        assert "text" in error_msg
        assert "expected str" in error_msg
        assert "got int" in error_msg


class TestStructEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()

    def test_empty_struct_instantiation(self):
        """Test instantiation with no arguments when fields are required."""
        fields = [StructField(name="required", type_hint=TypeHint(name="str"))]
        struct_def = StructDefinition(name="TestStruct", fields=fields)
        register_struct_from_ast(struct_def)

        # Empty instantiation should fail with clear message
        with pytest.raises(ValueError, match="Missing required fields"):
            create_struct_instance("TestStruct")

    def test_unknown_struct_type_error(self):
        """Test error when trying to instantiate unknown struct type."""
        with pytest.raises(ValueError, match="Unknown struct type 'NonExistent'"):
            create_struct_instance("NonExistent", field="value")

    def test_field_access_error_with_suggestions(self):
        """Test that field access errors provide helpful information."""
        fields = [
            StructField(name="valid_field", type_hint=TypeHint(name="str")),
            StructField(name="another_field", type_hint=TypeHint(name="int")),
        ]
        struct_def = StructDefinition(name="TestStruct", fields=fields)
        register_struct_from_ast(struct_def)

        instance = create_struct_instance("TestStruct", valid_field="test", another_field=42)

        # Accessing non-existent field should show available fields
        with pytest.raises(AttributeError) as exc_info:
            _ = instance.nonexistent_field

        error_msg = str(exc_info.value)
        assert "TestStruct" in error_msg
        assert "nonexistent_field" in error_msg
        assert "Available fields: ['another_field', 'valid_field']" in error_msg

    def test_field_access_with_typo_suggestions(self):
        """Test that typos in field names get helpful suggestions."""
        fields = [
            StructField(name="username", type_hint=TypeHint(name="str")),
            StructField(name="password", type_hint=TypeHint(name="str")),
            StructField(name="is_active", type_hint=TypeHint(name="bool")),
        ]
        struct_def = StructDefinition(name="User", fields=fields)
        register_struct_from_ast(struct_def)

        user = create_struct_instance("User", username="alice", password="secret", is_active=True)

        # Typo that should suggest the correct field
        with pytest.raises(AttributeError) as exc_info:
            _ = user.usernme  # missing 'a' in username

        error_msg = str(exc_info.value)
        assert "User" in error_msg
        assert "usernme" in error_msg
        assert "Did you mean 'username'?" in error_msg

        # Another typo test
        with pytest.raises(AttributeError) as exc_info:
            _ = user.pasword  # missing 's' in password

        error_msg = str(exc_info.value)
        assert "Did you mean 'password'?" in error_msg


class TestStructExecutionEdgeCases:
    """Test edge cases in Dana execution environment."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_struct_instantiation_with_type_errors(self):
        """Test struct instantiation type errors in Dana execution."""
        code = """
struct Point:
    x: int
    y: int

# This should fail with type error
local:point = Point(x="not_a_number", y=20)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert not result.success
        assert "Type validation failed" in str(result.error)
        assert "expected int" in str(result.error)
        assert "got str" in str(result.error)

    def test_field_assignment_type_errors(self):
        """Test field assignment type errors using direct method calls."""
        code = """
struct Point:
    x: int
    y: int

local:point = Point(x=10, y=20)
"""

        # Execute the struct creation first
        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success

        # Now test direct field assignment validation through Python
        assert result.final_context is not None
        point = result.final_context.get("local:point")
        assert isinstance(point, StructInstance)

        # Valid assignment should work
        point.x = 30
        assert point.x == 30

        # Invalid type assignment should fail
        with pytest.raises(TypeError, match="Field assignment failed.*y.*expected int.*got str"):
            point.y = "not_a_number"

    def test_nested_struct_validation(self):
        """Test validation of nested struct creation."""
        code = """
struct Point:
    x: int
    y: int

struct Circle:
    center: Point
    radius: float

local:point = Point(x=0, y=0)
local:circle = Circle(center=point, radius=5.0)

# This should fail - wrong type for center
local:bad_circle = Circle(center="not_a_point", radius=3.0)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert not result.success
        assert "Type validation failed" in str(result.error)
        assert "expected Point" in str(result.error)
