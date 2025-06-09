"""Tests for Dana module system core types."""

import pytest

from opendxa.dana.module.core.types import Module, ModuleCache, ModuleSpec, ModuleType


def test_module_creation(sample_module):
    """Test creating a Module instance."""
    module = Module(__file__=str(sample_module), __name__="sample")

    assert module.__name__ == "sample"
    assert module.__file__ == str(sample_module)
    assert module.__package__ == ""
    assert module.__dana_version__ == ""
    assert isinstance(module.__exports__, set)
    assert len(module.__exports__) == 0
    assert isinstance(module.__dict__, dict)


def test_module_attribute_access(sample_module):
    """Test module attribute access."""
    module = Module(__file__=str(sample_module), __name__="sample")

    # Test setting and getting attributes
    module.test_attr = "test value"
    assert module.test_attr == "test value"
    assert module.__dict__["test_attr"] == "test value"

    # Test attribute error
    with pytest.raises(AttributeError):
        _ = module.nonexistent_attr


def test_module_spec_creation(loader, sample_module):
    """Test creating a ModuleSpec instance."""
    spec = ModuleSpec(name="sample", loader=loader, origin=str(sample_module))

    assert spec.name == "sample"
    assert spec.loader is loader
    assert spec.origin == str(sample_module)
    assert isinstance(spec.cache, dict)
    assert spec.parent is None
    assert spec.has_location is True
    assert spec.submodule_search_locations is None


def test_module_type_constants():
    """Test ModuleType constants."""
    assert ModuleType.DANA == "dana"
    assert ModuleType.PYTHON == "python"
    assert ModuleType.GENERATED == "gen"
    assert ModuleType.HYBRID == "hybrid"


def test_module_cache(sample_module):
    """Test ModuleCache functionality."""
    cache = ModuleCache(timestamp=123.45, version_tag="1.0.0")

    assert cache.timestamp == 123.45
    assert cache.version_tag == "1.0.0"
    assert isinstance(cache.dependencies, dict)
    assert len(cache.dependencies) == 0

    # Test adding dependencies
    cache.dependencies["dep1"] = 100.0
    assert "dep1" in cache.dependencies
    assert cache.dependencies["dep1"] == 100.0


def test_module_package_handling(sample_package):
    """Test module package handling."""
    # Test package module
    pkg_module = Module(__file__=str(sample_package / "__init__.na"), __name__="sample_pkg")

    assert pkg_module.__name__ == "sample_pkg"
    assert pkg_module.__file__ == str(sample_package / "__init__.na")
    assert pkg_module.__package__ == "sample_pkg"

    # Test submodule
    submodule = Module(__file__=str(sample_package / "utils.na"), __name__="sample_pkg.utils")

    assert submodule.__name__ == "sample_pkg.utils"
    assert submodule.__file__ == str(sample_package / "utils.na")
    assert submodule.__package__ == "sample_pkg"


def test_module_spec_package_handling(loader, sample_package):
    """Test ModuleSpec package handling."""
    # Test package spec
    pkg_spec = ModuleSpec(name="sample_pkg", loader=loader, origin=str(sample_package / "__init__.na"))

    assert pkg_spec.name == "sample_pkg"
    assert pkg_spec.origin == str(sample_package / "__init__.na")
    assert pkg_spec.submodule_search_locations == [str(sample_package)]

    # Test submodule spec
    submodule_spec = ModuleSpec(name="sample_pkg.utils", loader=loader, origin=str(sample_package / "utils.na"), parent="sample_pkg")

    assert submodule_spec.name == "sample_pkg.utils"
    assert submodule_spec.origin == str(sample_package / "utils.na")
    assert submodule_spec.parent == "sample_pkg"
    assert submodule_spec.submodule_search_locations is None
