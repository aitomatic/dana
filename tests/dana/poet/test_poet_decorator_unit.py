"""
Unit tests for POET Dana-to-Dana enhancement implementation.

This module tests the core Dana enhancement functionality.
"""

from pathlib import Path

import pytest

from opendxa.dana.poet.decorator import POETDecorator, poet
from opendxa.dana.poet.enhancer import POETEnhancer
from opendxa.dana.poet.types import POETConfig


@pytest.mark.poet
class TestPOETEnhancer:
    """Unit tests for POET enhancer core functionality."""

    def test_enhancer_basic_functionality(self):
        """Test that POETEnhancer can enhance basic Dana code."""
        enhancer = POETEnhancer()

        # Simple Dana function
        dana_code = """
def add(a: int, b: int) -> int:
    return a + b
"""

        config = POETConfig(domain="test")
        enhanced_code = enhancer.enhance(dana_code, config)

        # Should return enhanced code
        assert isinstance(enhanced_code, str)
        assert len(enhanced_code) > len(dana_code)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhancer_invalid_dana_code(self):
        """Test that POETEnhancer raises error for invalid Dana code."""
        enhancer = POETEnhancer()

        # Invalid Dana code
        invalid_code = """
def add(a: int, b: int) -> int {
    return a + b
}
"""

        config = POETConfig(domain="test")
        with pytest.raises(RuntimeError, match="Invalid Dana code"):
            enhancer.enhance(invalid_code, config)

    def test_enhancer_with_domain_config(self):
        """Test that POETEnhancer uses domain configuration."""
        enhancer = POETEnhancer()

        dana_code = """
def multiply(x: int, y: int) -> int:
    return x * y
"""

        config = POETConfig(domain="mathematical_operations", retries=3, timeout=60.0)
        enhanced_code = enhancer.enhance(dana_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code


@pytest.mark.poet
class TestPOETDecorator:
    """Unit tests for POET decorator with Dana code."""

    def test_decorator_basic_application(self):
        """Test that poet factory can create POETDecorator with Dana code."""
        dana_code = """
def test_func(x: int) -> int:
    return x * 2
"""

        decorator = poet(dana_code, domain="test")

        # Should be a POETDecorator instance
        assert isinstance(decorator, POETDecorator)

        # Should have POET metadata
        assert hasattr(decorator, "_poet_metadata")

        # Metadata should contain expected values
        meta = decorator._poet_metadata
        domains = meta["domains"]
        assert isinstance(domains, list)
        assert "test" in domains
        assert meta["retries"] == 1  # Default value
        assert meta["timeout"] is None  # Default value
        assert meta["namespace"] == "local"  # Default value

    def test_decorator_with_parameters(self):
        """Test POET decorator with various parameters."""
        dana_code = """
def test_func(x: int) -> int:
    return x + 1
"""

        decorator = poet(dana_code, domain="custom", retries=3, timeout=60)

        meta = decorator._poet_metadata
        domains = meta["domains"]
        assert isinstance(domains, list)
        assert "custom" in domains
        assert meta["retries"] == 3
        assert meta["timeout"] == 60

    def test_decorator_enhanced_file_creation(self):
        """Test that decorator creates enhanced Dana files."""
        dana_code = """
def original_func(x: int, y: string) -> string:
    return f"{y}: {x}"
"""

        decorator = poet(dana_code, domain="test")

        # Should create enhanced file path
        assert decorator.enhanced_path == Path("dana") / "test_enhanced.na"

        # Should have wrapper
        assert hasattr(decorator, "wrapper")
        assert callable(decorator.wrapper)

    def test_decorator_metadata_access(self):
        """Test that decorator metadata is accessible."""
        dana_code = """
def func(x: int) -> int:
    return x * 2
"""

        decorator = poet(dana_code, domain="default")

        # Test metadata access
        meta = decorator._poet_metadata
        assert meta["domains"] == ["default"]
        assert meta["retries"] == 1
        assert meta["timeout"] is None
        assert meta["namespace"] == "local"
        assert meta["version"] == 1

    def test_decorator_repr(self):
        """Test that decorator has meaningful string representation."""
        dana_code = """
def func(x: int) -> int:
    return x * 2
"""

        decorator = poet(dana_code, domain="test")
        repr_str = repr(decorator)

        assert "POETDecorator" in repr_str
        assert "test" in repr_str

    def test_decorator_metadata_property(self):
        """Test that decorator provides metadata property."""
        dana_code = """
def func(x: int) -> int:
    return x * 2
"""

        decorator = poet(dana_code, domain="test")

        # Should have metadata property
        assert hasattr(decorator, "metadata")
        meta = decorator.metadata
        domains = meta["domains"]
        assert isinstance(domains, list)
        assert "test" in domains


@pytest.mark.poet
class TestPOETIntegration:
    """Integration tests for POET system."""

    def test_enhancer_decorator_integration(self):
        """Test that enhancer and decorator work together."""
        dana_code = """
def add(a: int, b: int) -> int:
    return a + b
"""

        # Create decorator
        decorator = poet(dana_code, domain="math")

        # Should create enhanced file when called
        decorator._ensure_enhanced_code_exists()

        # Enhanced file should exist
        assert decorator.enhanced_path.exists()

        # Enhanced file should contain enhanced code
        enhanced_content = decorator.enhanced_path.read_text()
        assert "# POET-enhanced Dana code" in enhanced_content
        assert dana_code.strip() in enhanced_content

    def test_cleanup_after_test(self):
        """Clean up any test files created."""
        # Remove any test files
        dana_dir = Path("dana")
        if dana_dir.exists():
            for file in dana_dir.glob("*_enhanced.na"):
                file.unlink()
