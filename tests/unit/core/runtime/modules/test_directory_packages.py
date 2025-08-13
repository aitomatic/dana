"""
Tests for directory package functionality in Dana module system.

This module tests the new directory package feature that allows directories
containing .na files to be treated as packages without requiring __init__.na files.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.__init__ import initialize_module_system, reset_module_system
from dana.core.lang.dana_sandbox import DanaSandbox


class TestDirectoryPackages:
    """Test class for directory package functionality."""

    def setup_method(self):
        """Reset module system before each test."""
        reset_module_system()

    def teardown_method(self):
        """Reset module system after each test."""
        reset_module_system()

    def test_simple_directory_package(self, tmp_path):
        """Test basic directory package without __init__.na."""
        # Create package structure
        pkg_dir = tmp_path / "simple_pkg"
        pkg_dir.mkdir()

        # Create module in package (no __init__.na)
        utils_file = pkg_dir / "utils.na"
        utils_file.write_text("""
def greet(name: str) -> str:
    return f"Hello, {name}!"

PACKAGE_VERSION = "1.0.0"
""")

        # Create driver module that imports from the directory package
        driver_file = tmp_path / "test_driver.na"
        driver_file.write_text("""
from simple_pkg.utils import greet, PACKAGE_VERSION

result = greet("World")
version = PACKAGE_VERSION
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        assert result.final_context.get("local:result") == "Hello, World!"
        assert result.final_context.get("local:version") == "1.0.0"

    def test_nested_directory_packages(self, tmp_path):
        """Test nested directory packages without __init__.na files."""
        # Create nested package structure
        root_pkg = tmp_path / "root_pkg"
        root_pkg.mkdir()

        sub_pkg = root_pkg / "sub_pkg"
        sub_pkg.mkdir()

        # Create modules in nested packages
        root_module = root_pkg / "root_utils.na"
        root_module.write_text("""
def root_function() -> str:
    return "From root package"
""")

        sub_module = sub_pkg / "sub_utils.na"
        sub_module.write_text("""
def sub_function() -> str:
    return "From sub package"
""")

        # Create driver module that imports from nested packages
        driver_file = tmp_path / "test_nested.na"
        driver_file.write_text("""
from root_pkg.root_utils import root_function
from root_pkg.sub_pkg.sub_utils import sub_function

root_result = root_function()
sub_result = sub_function()
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        assert result.final_context.get("local:root_result") == "From root package"
        assert result.final_context.get("local:sub_result") == "From sub package"

    def test_directory_package_import_as_module(self, tmp_path):
        """Test importing directory package as a module."""
        # Create package structure
        pkg_dir = tmp_path / "math_pkg"
        pkg_dir.mkdir()

        # Create multiple modules in package
        add_file = pkg_dir / "add.na"
        add_file.write_text("""
def add(a: int, b: int) -> int:
    return a + b
""")

        multiply_file = pkg_dir / "multiply.na"
        multiply_file.write_text("""
def multiply(a: int, b: int) -> int:
    return a * b
""")

        # Create driver module that imports the package and its submodules
        driver_file = tmp_path / "test_package_import.na"
        driver_file.write_text("""
import math_pkg.add
import math_pkg.multiply

add_result = math_pkg.add.add(5, 3)
mult_result = math_pkg.multiply.multiply(4, 7)
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        assert result.final_context.get("local:add_result") == 8
        assert result.final_context.get("local:mult_result") == 28

    def test_mixed_legacy_and_directory_packages(self, tmp_path):
        """Test mixing legacy __init__.na packages with new directory packages."""
        # Create legacy package with __init__.na
        legacy_pkg = tmp_path / "legacy_pkg"
        legacy_pkg.mkdir()

        legacy_init = legacy_pkg / "__init__.na"
        legacy_init.write_text("""
LEGACY_VERSION = "1.0.0"
""")

        legacy_module = legacy_pkg / "legacy_utils.na"
        legacy_module.write_text("""
def legacy_function() -> str:
    return "From legacy package"
""")

        # Create new directory package without __init__.na
        new_pkg = tmp_path / "new_pkg"
        new_pkg.mkdir()

        new_module = new_pkg / "new_utils.na"
        new_module.write_text("""
def new_function() -> str:
    return "From new package"
""")

        # Create driver module that imports from both
        driver_file = tmp_path / "test_mixed.na"
        driver_file.write_text("""
from legacy_pkg import LEGACY_VERSION
from legacy_pkg.legacy_utils import legacy_function
from new_pkg.new_utils import new_function

legacy_version = LEGACY_VERSION
legacy_result = legacy_function()
new_result = new_function()
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        assert result.final_context.get("local:legacy_version") == "1.0.0"
        assert result.final_context.get("local:legacy_result") == "From legacy package"
        assert result.final_context.get("local:new_result") == "From new package"

    def test_directory_package_relative_imports(self, tmp_path):
        """Test relative imports within directory packages."""
        # Create package structure
        pkg_dir = tmp_path / "rel_pkg"
        pkg_dir.mkdir()

        # Create base utility module
        base_file = pkg_dir / "base.na"
        base_file.write_text("""
def base_function() -> str:
    return "Base function"
""")

        # Create module that imports relatively
        derived_file = pkg_dir / "derived.na"
        derived_file.write_text("""
from .base import base_function

def derived_function() -> str:
    return f"Derived: {base_function()}"
""")

        # Create driver module
        driver_file = tmp_path / "test_relative.na"
        driver_file.write_text("""
from rel_pkg.derived import derived_function

result = derived_function()
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        result_value = str(result.final_context.get("local:result"))
        assert "Derived:" in result_value and "Base function" in result_value

    def test_empty_directory_not_package(self, tmp_path):
        """Test that empty directories are not considered packages."""
        # Create empty directory
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        # Create driver module that tries to import from empty directory
        driver_file = tmp_path / "test_empty.na"
        driver_file.write_text("""
import empty_dir.something
result = "Should not reach here"
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module - this should fail
        result = DanaSandbox.execute_file_once(driver_file)

        # This should fail because empty directory is not a valid package
        assert not result.success, "Expected failure but got success"
        assert "not found" in str(result.error)

    def test_directory_with_only_subdirectories(self, tmp_path):
        """Test directory package that contains only other packages."""
        # Create parent directory with no direct .na files
        parent_dir = tmp_path / "parent_pkg"
        parent_dir.mkdir()

        # Create child package with .na files
        child_dir = parent_dir / "child_pkg"
        child_dir.mkdir()

        child_module = child_dir / "child_utils.na"
        child_module.write_text("""
def child_function() -> str:
    return "From child package"
""")

        # Create driver module
        driver_file = tmp_path / "test_subdirs.na"
        driver_file.write_text("""
from parent_pkg.child_pkg.child_utils import child_function

result = child_function()
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        assert result.final_context.get("local:result") == "From child package"

    def test_deep_nesting_directory_packages(self, tmp_path):
        """Test deeply nested directory packages."""
        # Create deep nesting: a/b/c/d/e/module.na
        path_parts = ["deep_pkg", "level_a", "level_b", "level_c", "level_d"]
        current_path = tmp_path

        for part in path_parts:
            current_path = current_path / part
            current_path.mkdir()

        # Create module at the deepest level
        deep_module = current_path / "deep_utils.na"
        deep_module.write_text("""
def deep_function() -> str:
    return "From deep nested package"
""")

        # Create driver module
        driver_file = tmp_path / "test_deep.na"
        driver_file.write_text("""
from deep_pkg.level_a.level_b.level_c.level_d.deep_utils import deep_function

result = deep_function()
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.execute_file_once(driver_file)

        assert result.success, f"Expected success but got error: {result.error}"
        assert result.final_context.get("local:result") == "From deep nested package"
