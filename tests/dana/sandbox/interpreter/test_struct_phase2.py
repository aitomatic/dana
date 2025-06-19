"""
Tests for Phase 2: Struct execution functionality.

This module tests struct instantiation and field access execution in the Dana interpreter.
"""

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox, ExecutionResult
from opendxa.dana.sandbox.interpreter.struct_system import (
    StructInstance,
    StructTypeRegistry,
)


class TestStructExecution:
    """Test struct definition and instantiation execution."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_struct_definition_execution(self):
        """Test that struct definitions are properly executed and registered."""
        code = """
struct Point:
    x: int
    y: int
"""

        execution_result: ExecutionResult = self.sandbox.eval(code)

        # Execution should succeed
        assert execution_result.success is True

        # Struct definition should return None
        assert execution_result.result is None

        # But the struct should be registered
        assert StructTypeRegistry.exists("Point")

        # Check the registered struct type
        struct_type = StructTypeRegistry.get("Point")
        assert struct_type is not None
        assert struct_type.name == "Point"
        assert len(struct_type.fields) == 2
        assert "x" in struct_type.fields
        assert "y" in struct_type.fields
        assert struct_type.fields["x"] == "int"
        assert struct_type.fields["y"] == "int"

    def test_struct_instantiation_execution(self):
        """Test that struct instantiation creates StructInstance objects."""
        code = """
struct Point:
    x: int
    y: int

local:point = Point(x=10, y=20)
"""

        execution_result: ExecutionResult = self.sandbox.eval(code)

        # Check if execution succeeded
        if not execution_result.success:
            print(f"Execution failed: {execution_result.error}")
            raise AssertionError(f"Execution failed: {execution_result.error}")

        # Get the point variable from context
        assert execution_result.final_context is not None
        point = execution_result.final_context.get("local.point")
        assert point is not None

        # Should be a StructInstance
        assert isinstance(point, StructInstance)
        assert point.struct_type.name == "Point"
        assert point.get_field("x") == 10
        assert point.get_field("y") == 20

    def test_struct_field_access_execution(self):
        """Test field access on struct instances."""
        code = """
struct Point:
    x: int
    y: int

local:point = Point(x=10, y=20)
local:x_value = point.x
local:y_value = point.y
"""

        execution_result: ExecutionResult = self.sandbox.eval(code)

        # Check field access results
        assert execution_result.final_context is not None
        x_value = execution_result.final_context.get("local.x_value")
        y_value = execution_result.final_context.get("local.y_value")

        assert x_value == 10
        assert y_value == 20

    def test_struct_with_default_values(self):
        """Test struct instantiation with default field values."""
        code = """
struct User:
    name: str
    active: bool

local:user1 = User(name="Alice", active=true)
local:user2 = User(name="Bob", active=false)
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        user1 = result.final_context.get("local.user1")
        user2 = result.final_context.get("local.user2")

        assert user1 is not None
        assert user2 is not None
        assert isinstance(user1, StructInstance)
        assert user1.get_field("name") == "Alice"
        assert user1.get_field("active") is True

        assert isinstance(user2, StructInstance)
        assert user2.get_field("name") == "Bob"
        assert user2.get_field("active") is False

    def test_struct_field_modification(self):
        """Test modifying struct fields after instantiation."""
        code = """
struct Point:
    x: int
    y: int

local:point = Point(x=10, y=20)
local:original_x = point.x

# Modify the field (this will require field assignment implementation)
# For now, just test that we can access the field
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        point = result.final_context.get("local.point")
        original_x = result.final_context.get("local.original_x")

        assert point is not None
        assert isinstance(point, StructInstance)
        assert original_x == 10

    def test_struct_with_complex_field_types(self):
        """Test struct with various field types."""
        code = """
struct UserProfile:
    user_id: str
    age: int
    active: bool
    tags: list

local:profile = UserProfile(
    user_id="usr_123",
    age=25,
    active=true,
    tags=["admin", "premium"]
)
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        profile = result.final_context.get("local.profile")
        assert profile is not None

        assert isinstance(profile, StructInstance)
        assert profile.get_field("user_id") == "usr_123"
        assert profile.get_field("age") == 25
        assert profile.get_field("active") is True
        assert profile.get_field("tags") == ["admin", "premium"]

    def test_struct_instantiation_with_missing_fields(self):
        """Test error handling for missing required fields."""
        code = """
struct Point:
    x: int
    y: int

# This should fail - missing required field 'y'
local:point = Point(x=10)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert not result.success, "Expected struct instantiation to fail"
        assert "Missing required fields" in str(result.error), f"Expected missing fields error, got: {result.error}"

    def test_struct_instantiation_with_extra_fields(self):
        """Test error handling for extra unknown fields."""
        code = """
struct Point:
    x: int
    y: int

# This should fail - extra field 'z' not defined in struct
local:point = Point(x=10, y=20, z=30)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert not result.success, "Expected struct instantiation to fail"
        assert "Unknown fields" in str(result.error), f"Expected unknown fields error, got: {result.error}"

    def test_multiple_struct_definitions(self):
        """Test defining and using multiple struct types."""
        code = """
struct Point:
    x: int
    y: int

struct Circle:
    center: Point
    radius: float

local:center_point = Point(x=0, y=0)
local:circle = Circle(center=center_point, radius=5.0)
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        center_point = result.final_context.get("local.center_point")
        circle = result.final_context.get("local.circle")

        assert center_point is not None
        assert circle is not None
        assert isinstance(center_point, StructInstance)
        assert center_point.struct_type.name == "Point"

        assert isinstance(circle, StructInstance)
        assert circle.struct_type.name == "Circle"

        # The center field should contain the Point instance
        circle_center = circle.get_field("center")
        assert isinstance(circle_center, StructInstance)
        assert circle_center.struct_type.name == "Point"
        assert circle_center.get_field("x") == 0
        assert circle_center.get_field("y") == 0

        assert circle.get_field("radius") == 5.0


class TestStructIntegrationWithDanaFeatures:
    """Test struct integration with other Dana language features."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_struct_with_functions(self):
        """Test using structs with Dana functions."""
        code = """
struct Point:
    x: int
    y: int

def create_origin() -> Point:
    return Point(x=0, y=0)

local:origin = create_origin()
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        origin = result.final_context.get("local.origin")
        assert origin is not None

        assert isinstance(origin, StructInstance)
        assert origin.struct_type.name == "Point"
        assert origin.get_field("x") == 0
        assert origin.get_field("y") == 0

    def test_struct_in_conditionals(self):
        """Test using structs in conditional statements."""
        code = """
struct User:
    name: str
    active: bool

local:user = User(name="Alice", active=true)

if user.active:
    local:status = "active"
else:
    local:status = "inactive"
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        status = result.final_context.get("local.status")
        assert status == "active"

    def test_struct_in_loops(self):
        """Test using structs in loop constructs."""
        code = """
struct Point:
    x: int
    y: int

local:points = [Point(x=1, y=2), Point(x=3, y=4), Point(x=5, y=6)]
local:sum_x = 0

for point in points:
    local:sum_x = sum_x + point.x
"""

        result: ExecutionResult = self.sandbox.eval(code)

        assert result.final_context is not None
        sum_x = result.final_context.get("local.sum_x")
        assert sum_x == 9  # 1 + 3 + 5
