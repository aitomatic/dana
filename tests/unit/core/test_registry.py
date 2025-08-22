"""Tests for Dana module registry."""

import pytest

from dana.core.runtime.modules.errors import (
    CircularImportError,
    ModuleNotFoundError,
)
from dana.core.runtime.modules.types import Module, ModuleSpec
from dana.registry.module_registry import ModuleRegistry


def test_registry_creation():
    """Test that ModuleRegistry can be created."""
    reg1 = ModuleRegistry()
    reg2 = ModuleRegistry()
    # ModuleRegistry is no longer a singleton in the new registry system
    assert isinstance(reg1, ModuleRegistry)
    assert isinstance(reg2, ModuleRegistry)


def test_module_registration(registry, sample_module):
    """Test registering and retrieving modules."""
    module = Module(__file__=str(sample_module), __name__="sample")

    registry.register_module(module)
    assert registry.get_module("sample") is module
    assert "sample" in registry.get_loaded_modules()


def test_module_spec_registration(registry, loader, sample_module):
    """Test registering and retrieving module specs."""
    spec = ModuleSpec(name="sample", loader=loader, origin=str(sample_module))

    registry.register_spec(spec)
    assert registry.get_spec("sample") is spec
    assert "sample" in registry.get_specs()


def test_module_alias(registry, sample_module):
    """Test module aliasing."""
    module = Module(__file__=str(sample_module), __name__="sample")

    registry.register_module(module)
    registry.add_alias("alias_name", "sample")

    assert registry.get_module("alias_name") is module
    assert "alias_name" in registry.get_aliases()
    assert registry.resolve_alias("alias_name") == "sample"


def test_module_dependencies(registry, sample_package):
    """Test tracking module dependencies."""
    # Register package and submodule dependencies
    registry.add_dependency("sample_pkg.utils", "sample_pkg")
    registry.add_dependency("sample_pkg", "__builtins__")

    assert registry.get_dependencies("sample_pkg.utils") == {"sample_pkg"}
    assert registry.get_dependencies("sample_pkg") == {"__builtins__"}
    assert registry.get_dependencies("__builtins__") == set()


def test_circular_dependency_detection(registry):
    """Test detection of circular dependencies."""
    # Create a circular dependency chain
    registry.add_dependency("mod1", "mod2")
    registry.add_dependency("mod2", "mod3")
    registry.add_dependency("mod3", "mod1")

    with pytest.raises(CircularImportError) as exc_info:
        registry.check_circular_dependencies_legacy("mod1")

    assert exc_info.value.cycle == ["mod1", "mod2", "mod3", "mod1"]


def test_module_not_found(registry):
    """Test handling of non-existent modules."""
    with pytest.raises(ModuleNotFoundError):
        registry.get_module_or_raise("nonexistent")

    # get_spec returns None for non-existent modules, doesn't raise
    assert registry.get_spec("nonexistent") is None


def test_module_state_tracking(registry, sample_module):
    """Test module loading state tracking."""
    module_name = "sample"
    module = Module(__file__=str(sample_module), __name__=module_name)

    assert not registry.is_module_loading(module_name)

    registry.mark_module_loading(module_name)
    assert registry.is_module_loading(module_name)

    registry.register_module(module)
    registry.mark_module_loaded(module_name)
    assert not registry.is_module_loading(module_name)
    assert registry.is_module_loaded(module_name)


def test_registry_clear(registry, sample_module):
    """Test clearing the registry."""
    module = Module(__file__=str(sample_module), __name__="sample")

    registry.register_module(module)
    registry.add_alias("alias", "sample")
    registry.add_dependency("sample", "other_module")

    registry.clear_instance()

    assert not registry.get_loaded_modules()
    assert not registry.get_specs()
    assert not registry.get_aliases()
    assert not registry.get_dependencies("sample")
