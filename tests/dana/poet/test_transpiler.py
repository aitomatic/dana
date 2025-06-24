"""
Unit tests for POET enhancer implementation.

Tests the Dana-to-Dana enhancement functionality.
"""

import pytest

from opendxa.dana.poet.enhancer import POETEnhancer
from opendxa.dana.poet.types import POETConfig


class TestPOETEnhancer:
    """Test POET enhancer functionality."""

    @pytest.fixture
    def enhancer(self):
        """Create an enhancer instance."""
        return POETEnhancer()

    @pytest.fixture
    def basic_dana_code(self):
        """Sample Dana function code."""
        return """
def safe_divide(a: float, b: float) -> float:
    return a / b
"""

    def test_enhancer_instantiation(self, enhancer):
        """Test that enhancer can be instantiated."""
        assert enhancer is not None

    def test_enhance_basic_function(self, enhancer, basic_dana_code):
        """Test basic function enhancement."""
        config = POETConfig(domain="mathematical_operations", retries=2)

        enhanced_code = enhancer.enhance(basic_dana_code, config)

        # Should return enhanced code
        assert isinstance(enhanced_code, str)
        assert len(enhanced_code) > len(basic_dana_code)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert basic_dana_code.strip() in enhanced_code

    def test_enhance_with_different_domains(self, enhancer):
        """Test enhancement with different domain configurations."""
        dana_code = """
def calculate(x: float, y: float) -> float:
    return x * y
"""

        domains = ["mathematical_operations", "financial_calculations", "scientific_computing"]

        for domain in domains:
            config = POETConfig(domain=domain)
            enhanced_code = enhancer.enhance(dana_code, config)

            assert isinstance(enhanced_code, str)
            assert "# POET-enhanced Dana code" in enhanced_code
            assert dana_code.strip() in enhanced_code

    def test_enhance_with_custom_parameters(self, enhancer):
        """Test enhancement with custom configuration parameters."""
        dana_code = """
def complex_calculation(x: int, y: int, z: int) -> int:
    return x * y + z
"""

        config = POETConfig(domain="advanced_math", retries=5, timeout=120.0, enable_training=True)

        enhanced_code = enhancer.enhance(dana_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhance_complex_dana_code(self, enhancer):
        """Test enhancement with complex Dana code structures."""
        dana_code = """
struct Point:
    x: float
    y: float

def distance(p1: Point, p2: Point) -> float:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return sqrt(dx * dx + dy * dy)

def midpoint(p1: Point, p2: Point) -> Point:
    return Point(x=(p1.x + p2.x) / 2, y=(p1.y + p2.y) / 2)
"""

        config = POETConfig(domain="geometry")
        enhanced_code = enhancer.enhance(dana_code, config)

        # Should handle complex code without errors
        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhance_error_handling_invalid_code(self, enhancer):
        """Test error handling for invalid Dana code."""
        invalid_dana_code = """
def invalid_function(x: int) -> int {
    return x + 1
}
"""

        config = POETConfig(domain="test")

        # Should raise error for invalid Dana code
        with pytest.raises(RuntimeError, match="Invalid Dana code"):
            enhancer.enhance(invalid_dana_code, config)

    def test_enhance_error_handling_empty_code(self, enhancer):
        """Test error handling for empty Dana code."""
        empty_code = ""

        config = POETConfig(domain="test")

        # Should raise error for empty code
        with pytest.raises(RuntimeError, match="Invalid Dana code"):
            enhancer.enhance(empty_code, config)

    def test_enhance_error_handling_whitespace_only(self, enhancer):
        """Test error handling for whitespace-only Dana code."""
        whitespace_code = "   \n\t   "

        config = POETConfig(domain="test")

        # Should raise error for whitespace-only code
        with pytest.raises(RuntimeError, match="Invalid Dana code"):
            enhancer.enhance(whitespace_code, config)

    def test_enhance_with_multiple_functions(self, enhancer):
        """Test enhancement with multiple functions in the same code."""
        multi_function_code = """
def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b

def multiply(a: int, b: int) -> int:
    return a * b
"""

        config = POETConfig(domain="mathematical_operations")
        enhanced_code = enhancer.enhance(multi_function_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert multi_function_code.strip() in enhanced_code

    def test_enhance_with_structs_and_functions(self, enhancer):
        """Test enhancement with structs and functions."""
        struct_code = """
struct Rectangle:
    width: float
    height: float

def area(rect: Rectangle) -> float:
    return rect.width * rect.height

def perimeter(rect: Rectangle) -> float:
    return 2 * (rect.width + rect.height)
"""

        config = POETConfig(domain="geometry")
        enhanced_code = enhancer.enhance(struct_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert struct_code.strip() in enhanced_code

    def test_enhance_consistency(self, enhancer):
        """Test that enhancement is consistent for the same input."""
        dana_code = """
def test_func(x: int) -> int:
    return x * 2
"""

        config = POETConfig(domain="test", retries=3)

        # Enhance the same code multiple times
        enhanced1 = enhancer.enhance(dana_code, config)
        enhanced2 = enhancer.enhance(dana_code, config)

        # Should be consistent
        assert enhanced1 == enhanced2
        assert isinstance(enhanced1, str)
        assert "# POET-enhanced Dana code" in enhanced1
