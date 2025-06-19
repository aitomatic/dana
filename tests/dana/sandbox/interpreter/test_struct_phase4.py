"""
Tests for Phase 4: Advanced struct features and integration.

This module tests method syntax sugar (obj.method() → method(obj)), sophisticated
function dispatch, and integration with existing Dana features.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox
from opendxa.dana.sandbox.interpreter.struct_system import (
    StructInstance,
    StructTypeRegistry,
)


class TestMethodSyntaxTransformation:
    """Test obj.method() → method(obj) transformation."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_basic_method_syntax_transformation(self):
        """Test basic transformation of obj.method() to method(obj)."""
        code = """
struct Point:
    x: int
    y: int

def distance_from_origin(point: Point) -> float:
    import math.py
    return math.sqrt(point.x * point.x + point.y * point.y)

local:point = Point(x=3, y=4)
local:distance = distance_from_origin(point)
local:distance_method = point.distance_from_origin()
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        # Both calls should produce the same result
        distance_direct = result.final_context.get("local.distance")
        distance_method = result.final_context.get("local.distance_method")

        assert distance_direct == distance_method
        assert distance_direct == 5.0  # 3-4-5 triangle

    def test_method_with_arguments(self):
        """Test method transformation with additional arguments."""
        code = """
struct Point:
    x: int
    y: int

def add_offset(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

local:point = Point(x=10, y=20)
local:result_direct = add_offset(point, 5, 3)
local:result_method = point.add_offset(5, 3)
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        # Both results should be equivalent
        result_direct = result.final_context.get("local.result_direct")
        result_method = result.final_context.get("local.result_method")

        assert isinstance(result_direct, StructInstance)
        assert isinstance(result_method, StructInstance)
        assert result_direct.x == result_method.x == 15
        assert result_direct.y == result_method.y == 23

    def test_method_with_keyword_arguments(self):
        """Test method transformation with keyword arguments."""
        code = """
struct Rectangle:
    width: int
    height: int

def scale(rect: Rectangle, x_factor: float, y_factor: float) -> Rectangle:
    return Rectangle(width=int(rect.width * x_factor), height=int(rect.height * y_factor))

local:rect = Rectangle(width=10, height=20)
local:result_direct = scale(rect, x_factor=2.0, y_factor=1.5)
local:result_method = rect.scale(x_factor=2.0, y_factor=1.5)
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        result_direct = result.final_context.get("local.result_direct")
        result_method = result.final_context.get("local.result_method")

        assert isinstance(result_direct, StructInstance)
        assert isinstance(result_method, StructInstance)
        assert result_direct.width == result_method.width == 20  # 10 * 2.0
        assert result_direct.height == result_method.height == 30  # 20 * 1.5

    def test_polymorphic_method_dispatch(self):
        """Test that method transformation works with user-defined functions."""
        code = """
struct Point:
    x: int
    y: int

# Simple function that returns a constant (avoiding attribute access issues for now)
def get_type(point: Point) -> str:
    return "Point"

local:point = Point(x=1, y=2)

local:type_direct = get_type(point)
local:type_method = point.get_type()
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        # Both calls should produce the same result
        type_direct = result.final_context.get("local.type_direct")
        type_method = result.final_context.get("local.type_method")
        assert type_direct == type_method == "Point"

    def test_method_not_found_error(self):
        """Test error handling when method doesn't exist."""
        code = """
struct Point:
    x: int
    y: int

local:point = Point(x=1, y=2)
local:result = point.nonexistent_method()
"""

        result = self.sandbox.eval(code)
        assert not result.success
        # Check for the improved error message format
        assert "has no method" in str(result.error) or "not found" in str(result.error)


class TestStructMethodIntegration:
    """Test integration of struct methods with Dana features."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_struct_methods_in_loops(self):
        """Test using struct methods in loop constructs."""
        code = """
struct Number:
    value: int

def double(num: Number) -> Number:
    return Number(value=num.value * 2)

local:numbers = [Number(value=1), Number(value=2), Number(value=3)]
local:doubled = []

for num in numbers:
    local:doubled.append(num.double())

local:final_values = []
for doubled_num in doubled:
    local:final_values.append(doubled_num.value)
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        final_values = result.final_context.get("local.final_values")
        assert final_values == [2, 4, 6]

    def test_struct_methods_in_conditionals(self):
        """Test using struct methods in conditional statements."""
        code = """
struct Counter:
    count: int

def is_even(counter: Counter) -> bool:
    return counter.count % 2 == 0

def increment(counter: Counter) -> Counter:
    return Counter(count=counter.count + 1)

local:counter = Counter(count=5)

if counter.is_even():
    local:result = "even"
else:
    local:counter = counter.increment()
    local:result = "odd_incremented"

local:final_count = counter.count
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        result_type = result.final_context.get("local.result")
        final_count = result.final_context.get("local.final_count")

        assert result_type == "odd_incremented"
        assert final_count == 6

    def test_chained_method_calls(self):
        """Test chained method calls using transformation."""
        code = """
struct Builder:
    value: str

def add_text(builder: Builder, text: str) -> Builder:
    return Builder(value=builder.value + text)

def finalize(builder: Builder) -> str:
    return builder.value + "!"

local:builder = Builder(value="Hello")
local:step1 = builder.add_text(" ")
local:step2 = step1.add_text("World")
local:final = step2.finalize()
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        final_result = result.final_context.get("local.final")
        assert final_result == "Hello World!"

    def test_struct_methods_with_nested_structs(self):
        """Test methods on structs that contain other structs."""
        code = """
struct Point:
    x: int
    y: int

struct Line:
    start: Point
    end: Point

def length(line: Line) -> float:
    import math.py
    dx = line.end.x - line.start.x
    dy = line.end.y - line.start.y
    return math.sqrt(dx * dx + dy * dy)

def midpoint(line: Line) -> Point:
    mid_x = int((line.start.x + line.end.x) / 2)
    mid_y = int((line.start.y + line.end.y) / 2)
    return Point(x=mid_x, y=mid_y)

local:start = Point(x=0, y=0)
local:end = Point(x=6, y=8)
local:line = Line(start=start, end=end)

local:line_length = line.length()
local:line_midpoint = line.midpoint()
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        line_length = result.final_context.get("local.line_length")
        line_midpoint = result.final_context.get("local.line_midpoint")

        assert line_length == 10.0  # 6-8-10 triangle
        assert isinstance(line_midpoint, StructInstance)
        assert line_midpoint.x == 3
        assert line_midpoint.y == 4


class TestAdvancedStructFeatures:
    """Test advanced struct features and edge cases."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_struct_methods_with_multiple_signatures(self):
        """Test struct methods with multiple function signatures."""
        code = """
struct Vector:
    x: float
    y: float

# Different function names for different signatures (until proper overloading is implemented)
def scale_uniform(vector: Vector, factor: float) -> Vector:
    return Vector(x=vector.x * factor, y=vector.y * factor)

def scale_non_uniform(vector: Vector, x_factor: float, y_factor: float) -> Vector:
    return Vector(x=vector.x * x_factor, y=vector.y * y_factor)

local:vector = Vector(x=2.0, y=3.0)
local:uniform_scale = vector.scale_uniform(2.0)
local:non_uniform_scale = vector.scale_non_uniform(2.0, 3.0)
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        uniform_scale = result.final_context.get("local.uniform_scale")
        non_uniform_scale = result.final_context.get("local.non_uniform_scale")

        assert isinstance(uniform_scale, StructInstance)
        assert uniform_scale.x == 4.0  # 2.0 * 2.0
        assert uniform_scale.y == 6.0  # 3.0 * 2.0

        assert isinstance(non_uniform_scale, StructInstance)
        assert non_uniform_scale.x == 4.0  # 2.0 * 2.0
        assert non_uniform_scale.y == 9.0  # 3.0 * 3.0

    def test_struct_method_returning_different_types(self):
        """Test struct methods that return different types."""
        code = """
struct Data:
    values: list

def sum_values(data: Data) -> int:
    total = 0
    for value in data.values:
        total = total + value
    return total

def get_first(data: Data) -> int:
    if len(data.values) > 0:
        return data.values[0]
    return 0

def to_string(data: Data) -> str:
    return f"Data({data.values})"

local:data = Data(values=[1, 2, 3, 4, 5])
local:sum_result = data.sum_values()
local:first_result = data.get_first()
local:string_result = data.to_string()
"""

        result = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        sum_result = result.final_context.get("local.sum_result")
        first_result = result.final_context.get("local.first_result")
        string_result = result.final_context.get("local.string_result")

        assert sum_result == 15
        assert first_result == 1
        assert "Data([1, 2, 3, 4, 5])" in string_result
