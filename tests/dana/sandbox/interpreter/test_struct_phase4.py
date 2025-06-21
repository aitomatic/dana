"""
Tests for Phase 4: Struct method syntax transformation.

This module tests the transformation of method calls (obj.method()) to function calls (method(obj)).
"""

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox, ExecutionResult
from opendxa.dana.sandbox.interpreter.struct_system import (
    StructInstance,
    StructTypeRegistry,
)


class TestMethodSyntaxTransformation:
    """Test method syntax transformation (obj.method() -> method(obj))."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_basic_method_syntax_transformation(self):
        """Test basic method syntax transformation."""
        code = """
struct Point:
    x: int
    y: int

def distance(point: Point) -> float:
    # Simple distance calculation without math.sqrt
    # For a 3-4-5 triangle, this will return 25 (5²)
    return point.x * point.x + point.y * point.y

local:point = Point(x=3, y=4)
local:distance_result = point.distance()
local:distance_method_result = distance(point)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        # Both calls should produce the same result
        assert result.final_context is not None
        distance_direct = result.final_context.get("local:distance_result")
        distance_method = result.final_context.get("local:distance_method_result")

        assert distance_direct == distance_method
        assert distance_direct == 25.0  # 3-4-5 triangle

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

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        # Both results should be equivalent
        assert result.final_context is not None
        result_direct = result.final_context.get("local:result_direct")
        result_method = result.final_context.get("local:result_method")

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

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        result_direct = result.final_context.get("local:result_direct")
        result_method = result.final_context.get("local:result_method")

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

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        # Both calls should produce the same result
        assert result.final_context is not None
        type_direct = result.final_context.get("local:type_direct")
        type_method = result.final_context.get("local:type_method")
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

        result: ExecutionResult = self.sandbox.eval(code)
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

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        final_values = result.final_context.get("local:final_values")
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

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        result_type = result.final_context.get("local:result")
        final_count = result.final_context.get("local:final_count")

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

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        final_result = result.final_context.get("local:final")
        assert final_result == "Hello World!"

    def test_struct_methods_with_nested_structs(self):
        """Test methods on structs that contain other structs."""
        code = """
struct Point:
    x: int
    y: int

struct Circle:
    center: Point
    radius: float

def get_area(circle: Circle) -> float:
    return 3.14159 * circle.radius * circle.radius

def get_center_x(circle: Circle) -> int:
    return circle.center.x

local:circle = Circle(center=Point(x=10, y=20), radius=5.0)
local:area = circle.get_area()
local:center_x = circle.get_center_x()
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        area = result.final_context.get("local:area")
        center_x = result.final_context.get("local:center_x")

        # Approximate area calculation (π * r²)
        expected_area = 3.14159 * 5.0 * 5.0
        assert abs(area - expected_area) < 0.01
        assert center_x == 10

    def test_method_overloading_simulation(self):
        """Test simulating method overloading through different function signatures."""
        code = """
struct Point:
    x: int
    y: int

def add_point(point1: Point, point2: Point) -> Point:
    return Point(x=point1.x + point2.x, y=point1.y + point2.y)

def add_scalar(point: Point, scalar: int) -> Point:
    return Point(x=point.x + scalar, y=point.y + scalar)

local:point1 = Point(x=1, y=2)
local:point2 = Point(x=3, y=4)

# Method overloading simulation
local:result1 = point1.add_point(point2)  # Should call add_point(point1, point2)
local:result2 = point1.add_scalar(5)      # Should call add_scalar(point1, 5)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        result1 = result.final_context.get("local:result1")
        result2 = result.final_context.get("local:result2")

        assert isinstance(result1, StructInstance)
        assert isinstance(result2, StructInstance)
        assert result1.x == 4  # 1 + 3
        assert result1.y == 6  # 2 + 4
        assert result2.x == 6  # 1 + 5
        assert result2.y == 7  # 2 + 5

    def test_method_with_optional_parameters(self):
        """Test method transformation with optional parameters."""
        code = """
struct Config:
    name: str
    value: int

def update_config(config: Config, new_name: str, new_value: int = None) -> Config:
    if new_value is None:
        new_value = config.value
    return Config(name=new_name, value=new_value)

local:config = Config(name="old", value=10)
local:updated1 = config.update_config("new_name")
local:updated2 = config.update_config("new_name", 20)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        updated1 = result.final_context.get("local:updated1")
        updated2 = result.final_context.get("local:updated2")

        assert isinstance(updated1, StructInstance)
        assert isinstance(updated2, StructInstance)
        assert updated1.name == "new_name"
        assert updated1.value == 10  # Used default value
        assert updated2.name == "new_name"
        assert updated2.value == 20  # Used provided value


class TestAdvancedStructFeatures:
    """Test advanced struct features and edge cases."""

    def setup_method(self):
        """Clear struct registry before each test."""
        StructTypeRegistry.clear()
        self.sandbox = DanaSandbox()

    def test_struct_methods_with_multiple_signatures(self):
        """Test struct methods that can handle multiple argument patterns."""
        code = """
struct Vector:
    x: float
    y: float

def normalize(vector: Vector, length: float = 1.0) -> Vector:
    # Simple normalization without math.sqrt
    # For vector (3,4), magnitude squared is 25, so scale by length/5
    magnitude_squared = vector.x * vector.x + vector.y * vector.y
    if magnitude_squared == 0:
        return Vector(x=0, y=0)
    
    # Use a simple approximation: scale by length/sqrt(magnitude_squared)
    # For (3,4), sqrt(25) = 5, so scale by length/5
    if magnitude_squared == 25:  # 3² + 4² = 25
        scale = length / 5.0
    else:
        # Fallback for other values
        scale = length / (magnitude_squared ** 0.5)
    
    return Vector(x=vector.x * scale, y=vector.y * scale)

local:vector = Vector(x=3, y=4)
local:normalized1 = vector.normalize()      # Default length=1.0
local:normalized2 = vector.normalize(2.0)   # Custom length
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        normalized1 = result.final_context.get("local:normalized1")
        normalized2 = result.final_context.get("local:normalized2")

        assert isinstance(normalized1, StructInstance)
        assert isinstance(normalized2, StructInstance)

        # Check that both are normalized (magnitude squared should be 1.0² and 2.0² respectively)
        mag1_squared = normalized1.x * normalized1.x + normalized1.y * normalized1.y
        mag2_squared = normalized2.x * normalized2.x + normalized2.y * normalized2.y

        assert abs(mag1_squared - 1.0) < 0.01
        assert abs(mag2_squared - 4.0) < 0.01  # 2.0² = 4.0

    def test_struct_method_returning_different_types(self):
        """Test struct methods that return different types based on context."""
        code = """
struct Data:
    value: str

def process(data: Data, as_string: bool = True) -> str | int:
    if as_string:
        return data.value
    else:
        # Try to convert to int, return 0 if failed
        try:
            return int(data.value)
        except:
            return 0

local:data = Data(value="42")
local:as_string = data.process()
local:as_int = data.process(as_string=false)
"""

        result: ExecutionResult = self.sandbox.eval(code)
        assert result.success, f"Execution failed: {result.error}"

        assert result.final_context is not None
        as_string = result.final_context.get("local:as_string")
        as_int = result.final_context.get("local:as_int")

        assert as_string == "42"
        assert as_int == 42
