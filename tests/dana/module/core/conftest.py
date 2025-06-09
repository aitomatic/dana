"""Shared fixtures for Dana module system tests."""

from pathlib import Path

import pytest

from opendxa.dana.module.core.loader import ModuleLoader
from opendxa.dana.module.core.registry import ModuleRegistry


@pytest.fixture
def registry():
    """Create a fresh ModuleRegistry for each test."""
    reg = ModuleRegistry()
    reg.clear()  # Ensure clean state
    return reg


@pytest.fixture
def search_paths(tmp_path):
    """Create and return a list of search paths."""
    paths = [str(tmp_path / "modules"), str(tmp_path / "packages"), str(Path.cwd())]
    # Create directories
    for path in paths[:-1]:  # Skip cwd
        Path(path).mkdir(parents=True, exist_ok=True)
    return paths


@pytest.fixture
def loader(registry, search_paths):
    """Create a ModuleLoader with test registry and search paths."""
    return ModuleLoader(search_paths=search_paths, registry=registry)


@pytest.fixture
def sample_module(tmp_path):
    """Create a sample Dana module file."""
    module_dir = tmp_path / "modules"
    module_dir.mkdir(exist_ok=True)

    module_path = module_dir / "sample.na"
    module_path.write_text(
        """
# Sample Dana module
VERSION: str = "1.0.0"
MESSAGE: str = "Hello from sample module!"

def greet(name: str) -> str:
    return f"Hello, {name}!"

export VERSION
export MESSAGE
export greet
"""
    )
    return module_path


@pytest.fixture
def sample_package(tmp_path):
    """Create a sample Dana package."""
    pkg_dir = tmp_path / "packages" / "sample_pkg"
    pkg_dir.mkdir(parents=True)

    # Create __init__.na
    init_file = pkg_dir / "__init__.na"
    init_file.write_text(
        """
# Sample package init
PACKAGE_NAME: str = "sample_pkg"
VERSION: str = "1.0.0"

export PACKAGE_NAME
export VERSION
"""
    )

    # Create a submodule
    submodule = pkg_dir / "utils.na"
    submodule.write_text(
        """
# Utility functions

def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

export add
export multiply
"""
    )

    return pkg_dir
