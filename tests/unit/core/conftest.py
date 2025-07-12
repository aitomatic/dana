import pytest

from dana.core.runtime.modules.core.loader import ModuleLoader
from dana.core.runtime.modules.core.registry import ModuleRegistry


def pytest_addoption(parser):
    parser.addoption("--ux-review", action="store_true", help="Review UX outputs instead of asserting")


@pytest.fixture
def sample_module(tmp_path):
    """Create a sample Dana module for testing."""
    module_file = tmp_path / "sample.na"
    module_content = """# Sample Dana module for testing
VERSION = "1.0.0"
MESSAGE = "Hello from sample module!"

def greet(name: str) -> str:
    return f"Hello, {name}!"

# Export specific items
__exports__ = {"VERSION", "MESSAGE", "greet"}
"""
    module_file.write_text(module_content)
    return module_file


@pytest.fixture
def sample_package(tmp_path):
    """Create a sample Dana package for testing."""
    package_dir = tmp_path / "sample_pkg"
    package_dir.mkdir()

    # Create __init__.na
    init_file = package_dir / "__init__.na"
    init_content = """# Sample package __init__.na
PACKAGE_NAME = "sample_pkg"
VERSION = "1.0.0"

__exports__ = {"PACKAGE_NAME", "VERSION"}
"""
    init_file.write_text(init_content)

    # Create utils.na submodule
    utils_file = package_dir / "utils.na"
    utils_content = """# Sample package utils module
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

__exports__ = {"add", "multiply"}
"""
    utils_file.write_text(utils_content)

    return package_dir


@pytest.fixture
def search_paths(tmp_path):
    """Create search paths for module loading tests."""
    # Include the tmp_path itself so that modules created there can be found
    return [str(tmp_path)]


@pytest.fixture
def loader(search_paths, registry):
    """Create a ModuleLoader instance for testing."""
    return ModuleLoader(search_paths=search_paths, registry=registry)


@pytest.fixture
def registry():
    """Create a ModuleRegistry instance for testing."""
    return ModuleRegistry()
