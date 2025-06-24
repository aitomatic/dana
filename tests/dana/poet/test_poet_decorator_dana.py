"""
Tests for POET Dana-to-Dana enhancement system.

This module tests the POET enhancement functionality for Dana code.
"""

from pathlib import Path

import pytest

from opendxa.dana.poet.decorator import POETDecorator, poet


@pytest.mark.poet
class TestPOETDanaEnhancement:
    """Test POET Dana-to-Dana enhancement functionality."""

    def test_basic_dana_enhancement(self):
        """Test basic POET enhancement of Dana code."""
        dana_code = """
def add(a: int, b: int) -> int:
    return a + b
"""

        # Create POET decorator with Dana code
        decorator = poet(dana_code, domain="math_operations")

        # Should be a POETDecorator instance
        assert isinstance(decorator, POETDecorator)

        # Should have metadata
        assert hasattr(decorator, "_poet_metadata")
        meta = decorator._poet_metadata
        domains = meta["domains"]
        assert isinstance(domains, list)
        assert "math_operations" in domains

    def test_enhanced_file_creation(self):
        """Test that enhanced Dana files are created."""
        dana_code = """
def multiply(x: int, y: int) -> int:
    return x * y
"""

        decorator = poet(dana_code, domain="test_math")

        # Should create enhanced file when needed
        decorator._ensure_enhanced_code_exists()

        # Enhanced file should exist
        assert decorator.enhanced_path.exists()

        # Enhanced file should contain enhanced code
        enhanced_content = decorator.enhanced_path.read_text()
        assert "# POET-enhanced Dana code" in enhanced_content
        assert dana_code.strip() in enhanced_content

    def test_enhancer_with_different_domains(self):
        """Test POET enhancer with different domain configurations."""
        dana_code = """
def divide(a: float, b: float) -> float:
    return a / b
"""

        # Test with different domains
        domains = ["mathematical_operations", "financial_calculations", "scientific_computing"]

        for domain in domains:
            decorator = poet(dana_code, domain=domain)
            meta = decorator._poet_metadata
            domains_list = meta["domains"]
            assert isinstance(domains_list, list)
            assert domain in domains_list

    def test_enhancer_with_custom_parameters(self):
        """Test POET enhancer with custom configuration parameters."""
        dana_code = """
def complex_calculation(x: int, y: int, z: int) -> int:
    return x * y + z
"""

        decorator = poet(dana_code, domain="advanced_math", retries=5, timeout=120.0, enable_training=True)

        meta = decorator._poet_metadata
        assert meta["retries"] == 5
        assert meta["timeout"] == 120.0
        domains = meta["domains"]
        assert isinstance(domains, list)
        assert "advanced_math" in domains

    def test_enhancer_with_complex_dana_code(self):
        """Test POET enhancer with more complex Dana code structures."""
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

        decorator = poet(dana_code, domain="geometry")

        # Should handle complex code without errors
        assert isinstance(decorator, POETDecorator)

        # Should create enhanced file
        decorator._ensure_enhanced_code_exists()
        assert decorator.enhanced_path.exists()

    def test_enhancer_file_path_management(self):
        """Test that enhanced file paths are managed correctly."""
        dana_code = """
def test_func(x: int) -> int:
    return x * 2
"""

        # Test with different domains
        decorator1 = poet(dana_code, domain="domain1")
        decorator2 = poet(dana_code, domain="domain2")

        # Should have different file paths
        assert decorator1.enhanced_path != decorator2.enhanced_path
        assert "domain1_enhanced.na" in str(decorator1.enhanced_path)
        assert "domain2_enhanced.na" in str(decorator2.enhanced_path)

    def test_enhancer_metadata_consistency(self):
        """Test that metadata is consistent across different decorator instances."""
        dana_code = """
def consistent_func(x: int) -> int:
    return x + 10
"""

        # Create multiple decorators with same configuration
        decorator1 = poet(dana_code, domain="consistency_test", retries=3)
        decorator2 = poet(dana_code, domain="consistency_test", retries=3)

        # Metadata should be consistent
        meta1 = decorator1._poet_metadata
        meta2 = decorator2._poet_metadata

        assert meta1["domains"] == meta2["domains"]
        assert meta1["retries"] == meta2["retries"]
        assert meta1["timeout"] == meta2["timeout"]
        assert meta1["namespace"] == meta2["namespace"]
        assert meta1["version"] == meta2["version"]

    def test_cleanup_after_tests(self):
        """Clean up any test files created."""
        # Remove any test files
        dana_dir = Path("dana")
        if dana_dir.exists():
            for file in dana_dir.glob("*_enhanced.na"):
                file.unlink()
