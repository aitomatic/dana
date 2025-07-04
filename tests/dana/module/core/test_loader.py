"""Tests for Dana module loader."""

import pytest

from dana.core.runtime.modules.core.errors import (
    SyntaxError,
)
from dana.core.runtime.modules.core.types import Module, ModuleSpec


def test_loader_find_spec(loader, sample_module, search_paths):
    """Test finding module specs."""
    spec = loader.find_spec("sample", None)

    assert spec is not None
    assert spec.name == "sample"
    assert spec.loader is loader
    assert spec.origin == str(sample_module)
    assert spec.has_location is True


def test_loader_create_module(loader):
    """Test creating a module from a spec."""
    spec = ModuleSpec(name="test_module", loader=loader, origin="/path/to/module.na")

    module = loader.create_module(spec)

    assert isinstance(module, Module)
    assert module.__name__ == "test_module"
    assert module.__file__ == "/path/to/module.na"
    assert module.__spec__ is spec


def test_loader_exec_module(loader, sample_module):
    """Test executing a module."""
    spec = ModuleSpec(name="sample", loader=loader, origin=str(sample_module))
    module = loader.create_module(spec)

    loader.exec_module(module)

    assert hasattr(module, "VERSION")
    assert module.VERSION == "1.0.0"
    assert hasattr(module, "MESSAGE")
    assert module.MESSAGE == "Hello from sample module!"
    assert hasattr(module, "greet")
    assert module.greet("Dana") == "Hello, Dana!"
    assert "VERSION" in module.__exports__
    assert "MESSAGE" in module.__exports__
    assert "greet" in module.__exports__


def test_loader_invalid_module(loader, tmp_path):
    """Test handling invalid module syntax."""
    invalid_module = tmp_path / "invalid.na"
    invalid_module.write_text(
        """
# Invalid Dana syntax
def broken function() -> str  # Missing colon
    return "This won't work"
"""
    )

    spec = ModuleSpec(name="invalid", loader=loader, origin=str(invalid_module))
    module = loader.create_module(spec)

    with pytest.raises(SyntaxError):
        loader.exec_module(module)


def test_loader_module_not_found(loader):
    """Test handling non-existent modules."""
    # find_spec should return None for non-existent modules (not raise)
    # This is the correct behavior for MetaPathFinder protocol
    spec = loader.find_spec("nonexistent_module", None)
    assert spec is None


def test_loader_package_handling(loader, sample_package):
    """Test handling of package modules."""
    # Test package initialization
    pkg_spec = loader.find_spec("sample_pkg", None)
    assert pkg_spec is not None
    assert pkg_spec.name == "sample_pkg"
    assert pkg_spec.origin == str(sample_package / "__init__.na")
    assert pkg_spec.submodule_search_locations == [str(sample_package)]

    # Test package module
    pkg_module = loader.create_module(pkg_spec)
    loader.exec_module(pkg_module)
    assert pkg_module.PACKAGE_NAME == "sample_pkg"
    assert pkg_module.VERSION == "1.0.0"

    # Test submodule
    submodule_spec = loader.find_spec("sample_pkg.utils", None)
    assert submodule_spec is not None
    assert submodule_spec.name == "sample_pkg.utils"
    assert submodule_spec.origin == str(sample_package / "utils.na")

    submodule = loader.create_module(submodule_spec)
    loader.exec_module(submodule)
    assert submodule.add(2, 3) == 5
    assert submodule.multiply(4, 5) == 20
