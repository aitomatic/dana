"""
Tests for directory package functionality in Python-to-Dana integration.

This module tests that directory packages work correctly when imported from Python,
ensuring the Python integration properly handles the new directory package feature.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest
import sys
from pathlib import Path

from dana.integrations.python.to_dana import enable_dana_imports, disable_dana_imports


class TestDirectoryPackagesPythonIntegration:
    """Test class for directory package Python integration."""

    def setup_method(self):
        """Set up for each test."""
        # Ensure dana imports are disabled initially
        disable_dana_imports()
        
        # Clean up any existing modules from previous tests
        modules_to_remove = [name for name in sys.modules.keys() if name.startswith('test_')]
        for module_name in modules_to_remove:
            del sys.modules[module_name]

    def teardown_method(self):
        """Clean up after each test."""
        disable_dana_imports()
        
        # Clean up any test modules
        modules_to_remove = [name for name in sys.modules.keys() if name.startswith('test_')]
        for module_name in modules_to_remove:
            del sys.modules[module_name]

    def test_python_import_directory_package(self, tmp_path):
        """Test importing Dana directory package from Python."""
        # Create package structure
        pkg_dir = tmp_path / "test_python_pkg"
        pkg_dir.mkdir()

        # Create module in package (no __init__.na)
        utils_file = pkg_dir / "math_utils.na"
        utils_file.write_text("""
def add_numbers(a: int, b: int) -> int:
    return a + b

def multiply_numbers(a: int, b: int) -> int:
    return a * b

MATH_CONSTANT = 42
""")

        # Enable Dana imports for this test path
        enable_dana_imports([str(tmp_path)])

        try:
            # Import the Dana module from Python
            from test_python_pkg.math_utils import add_numbers, multiply_numbers, MATH_CONSTANT

            # Test function calls
            assert add_numbers(5, 3) == 8
            assert multiply_numbers(4, 7) == 28
            assert MATH_CONSTANT == 42

        finally:
            disable_dana_imports()

    def test_python_import_nested_directory_packages(self, tmp_path):
        """Test importing nested Dana directory packages from Python."""
        # Create nested package structure
        root_pkg = tmp_path / "test_nested_pkg"
        root_pkg.mkdir()
        
        sub_pkg = root_pkg / "subpackage"
        sub_pkg.mkdir()

        # Create modules in nested packages
        root_module = root_pkg / "root_module.na"
        root_module.write_text("""
def root_function() -> str:
    return "Hello from root"
""")

        sub_module = sub_pkg / "sub_module.na"
        sub_module.write_text("""
def sub_function() -> str:
    return "Hello from sub"
""")

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Import from nested packages
            from test_nested_pkg.root_module import root_function
            from test_nested_pkg.subpackage.sub_module import sub_function

            # Test function calls
            assert root_function() == "Hello from root"
            assert sub_function() == "Hello from sub"

        finally:
            disable_dana_imports()

    def test_python_import_directory_package_as_module(self, tmp_path):
        """Test importing Dana directory package as a module object from Python."""
        # Create package structure
        pkg_dir = tmp_path / "test_module_pkg"
        pkg_dir.mkdir()

        # Create multiple modules in package
        first_file = pkg_dir / "first.na"
        first_file.write_text("""
def first_func() -> str:
    return "First function"
""")

        second_file = pkg_dir / "second.na"
        second_file.write_text("""
def second_func() -> str:
    return "Second function"
""")

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Import package and submodules
            import test_module_pkg.first
            import test_module_pkg.second

            # Test accessing functions through module objects
            assert test_module_pkg.first.first_func() == "First function"
            assert test_module_pkg.second.second_func() == "Second function"

        finally:
            disable_dana_imports()

    def test_python_mixed_legacy_and_directory_packages(self, tmp_path):
        """Test Python importing both legacy and directory packages."""
        # Create legacy package with __init__.na
        legacy_pkg = tmp_path / "test_legacy_pkg"
        legacy_pkg.mkdir()
        
        legacy_init = legacy_pkg / "__init__.na"
        legacy_init.write_text("""
LEGACY_VALUE = "legacy"
""")

        legacy_module = legacy_pkg / "legacy_mod.na"
        legacy_module.write_text("""
def legacy_func() -> str:
    return "Legacy function"
""")

        # Create new directory package without __init__.na
        new_pkg = tmp_path / "test_new_pkg"
        new_pkg.mkdir()

        new_module = new_pkg / "new_mod.na"
        new_module.write_text("""
def new_func() -> str:
    return "New function"
""")

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Import from both package types
            from test_legacy_pkg import LEGACY_VALUE
            from test_legacy_pkg.legacy_mod import legacy_func
            from test_new_pkg.new_mod import new_func

            # Test both work correctly
            assert LEGACY_VALUE == "legacy"
            assert legacy_func() == "Legacy function"
            assert new_func() == "New function"

        finally:
            disable_dana_imports()

    def test_python_directory_package_with_subdirs_only(self, tmp_path):
        """Test Python importing directory package that has only subdirectories."""
        # Create parent directory with no direct .na files
        parent_dir = tmp_path / "test_parent_pkg"
        parent_dir.mkdir()

        # Create child package with .na files
        child_dir = parent_dir / "child"
        child_dir.mkdir()

        child_module = child_dir / "child_mod.na"
        child_module.write_text("""
def child_function() -> str:
    return "Child function"
""")

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Import from nested package
            from test_parent_pkg.child.child_mod import child_function

            # Test function call
            assert child_function() == "Child function"

        finally:
            disable_dana_imports()

    def test_python_directory_package_error_handling(self, tmp_path):
        """Test error handling when Python tries to import invalid directory packages."""
        # Create empty directory (should not be importable)
        empty_dir = tmp_path / "test_empty_pkg"
        empty_dir.mkdir()

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Try to import from empty directory - should fail
            with pytest.raises(ModuleNotFoundError):
                import test_empty_pkg.nonexistent

        finally:
            disable_dana_imports()

    def test_python_directory_package_deep_nesting(self, tmp_path):
        """Test Python importing deeply nested directory packages."""
        # Create deep nesting
        path_parts = ["test_deep_pkg", "level1", "level2", "level3"]
        current_path = tmp_path
        
        for part in path_parts:
            current_path = current_path / part
            current_path.mkdir()

        # Create module at the deepest level
        deep_module = current_path / "deep_mod.na"
        deep_module.write_text("""
def deep_function() -> str:
    return "Deep nested function"
""")

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Import from deeply nested package
            from test_deep_pkg.level1.level2.level3.deep_mod import deep_function

            # Test function call
            assert deep_function() == "Deep nested function"

        finally:
            disable_dana_imports()

    def test_python_directory_package_attributes(self, tmp_path):
        """Test that directory packages have correct Python module attributes."""
        # Create package structure
        pkg_dir = tmp_path / "test_attrs_pkg"
        pkg_dir.mkdir()

        # Create module in package
        mod_file = pkg_dir / "test_mod.na"
        mod_file.write_text("""
def test_func() -> str:
    return "Test function"
""")

        # Enable Dana imports
        enable_dana_imports([str(tmp_path)])

        try:
            # Import the package and module
            import test_attrs_pkg.test_mod

            # Check module attributes
            module = test_attrs_pkg.test_mod
            assert hasattr(module, '__name__')
            assert hasattr(module, '__file__')
            assert hasattr(module, '__package__')
            
            assert module.__name__ == 'test_attrs_pkg.test_mod'
            assert module.__package__ == 'test_attrs_pkg'
            assert module.__file__.endswith('test_mod.na')

        finally:
            disable_dana_imports()