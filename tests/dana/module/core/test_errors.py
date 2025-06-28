"""Tests for Dana module system error types."""

from pathlib import Path

from opendxa.dana.module.core.errors import (
    CircularImportError,
    CompileError,
    ImportError,
    LinkageError,
    ModuleError,
    ModuleNotFoundError,
    ResourceError,
    SecurityError,
    SyntaxError,
    VersionError,
)


def test_module_error():
    """Test base ModuleError."""
    error = ModuleError(
        message="Test error", module_name="test_module", file_path="/path/to/module.na", line_number=42, source_line="def test_function():"
    )

    assert "Test error" in str(error)
    assert "test_module" in str(error)
    assert "/path/to/module.na" in str(error)
    assert "Line 42" in str(error)
    assert "def test_function():" in str(error)


def test_module_not_found_error():
    """Test ModuleNotFoundError."""
    paths = ["/path1", "/path2"]
    error = ModuleNotFoundError(name="missing_module", searched_paths=paths)

    assert "missing_module" in str(error)
    assert error.searched_paths == paths


def test_circular_import_error():
    """Test CircularImportError."""
    cycle = ["mod1", "mod2", "mod3", "mod1"]
    error = CircularImportError(cycle)

    assert all(mod in str(error) for mod in cycle)
    assert error.cycle == cycle
    assert error.module_name == cycle[0]


def test_version_error():
    """Test VersionError."""
    error = VersionError(module_name="test_module", required_version="1.0.0", current_version="0.9.0")

    assert "test_module" in str(error)
    assert "1.0.0" in str(error)
    assert "0.9.0" in str(error)
    assert error.required_version == "1.0.0"
    assert error.current_version == "0.9.0"


def test_error_inheritance():
    """Test error class inheritance."""
    assert issubclass(ModuleNotFoundError, ModuleError)
    assert issubclass(ImportError, ModuleError)
    assert issubclass(CircularImportError, ImportError)
    assert issubclass(VersionError, ModuleError)
    assert issubclass(SyntaxError, ModuleError)
    assert issubclass(CompileError, ModuleError)
    assert issubclass(LinkageError, ModuleError)
    assert issubclass(SecurityError, ModuleError)
    assert issubclass(ResourceError, ModuleError)


def test_error_with_partial_info():
    """Test ModuleError with partial information."""
    error = ModuleError(message="Test error", module_name="test_module")

    assert "Test error" in str(error)
    assert "test_module" in str(error)
    assert "Line" not in str(error)
    assert error.line_number is None
    assert error.source_line is None


def test_error_with_path_types():
    """Test ModuleError with different path types."""
    # Test with string path
    error1 = ModuleError("Test", file_path="/path/to/module.na")
    assert "/path/to/module.na" in str(error1)

    # Test with Path object
    error2 = ModuleError("Test", file_path=Path("/path/to/module.na"))
    assert "/path/to/module.na" in str(error2)
