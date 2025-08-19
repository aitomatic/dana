#!/usr/bin/env python3
"""
Tests for relative import functionality in Dana.

This module tests relative imports like 'from . import submod' and 'from .. import parent'
which were previously not covered in the test suite.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from pathlib import Path

from dana.core.lang.dana_sandbox import DanaSandbox


class TestRelativeImports:
    """Test class for relative import functionality."""

    def setup_method(self):
        """Set up test fixtures with relative import test modules."""
        self.sandbox = DanaSandbox()

        # Set up test modules path for relative imports
        test_modules_path = Path(__file__).parent / "test_modules_relative"
        self.test_modules_path = str(test_modules_path.resolve())

        # Create test module structure if it doesn't exist
        self._create_test_modules()

        # Add to DANAPATH
        os.environ.setdefault("DANAPATH", "")
        if self.test_modules_path not in os.environ["DANAPATH"]:
            os.environ["DANAPATH"] = f"{self.test_modules_path}{os.pathsep}{os.environ['DANAPATH']}"

        # Reset module system
        from dana.__init__ import initialize_module_system, reset_module_system

        reset_module_system()
        initialize_module_system()

    def _create_test_modules(self):
        """Create test module structure for relative imports."""
        base_path = Path(__file__).parent / "test_modules_relative"
        base_path.mkdir(exist_ok=True)

        # Create test_pkg package with submodules
        pkg_path = base_path / "test_pkg"
        pkg_path.mkdir(exist_ok=True)

        # test_pkg/__init__.na - tests 'from . import submod'
        (pkg_path / "__init__.na").write_text("""
# Test relative imports in package __init__.na
from . import submod
from . import helper
from . import nested

I_AM = "test_pkg"
""")

        # test_pkg/submod.na
        (pkg_path / "submod.na").write_text("""
# Simple submodule
I_AM = "test_pkg.submod"

def submod_function():
    return "Hello from submod"
""")

        # test_pkg/helper.na
        (pkg_path / "helper.na").write_text("""
# Helper submodule
I_AM = "test_pkg.helper"

def helper_function():
    return "Helper function"
""")

        # Create nested package for testing parent imports
        nested_path = pkg_path / "nested"
        nested_path.mkdir(exist_ok=True)

        # test_pkg/nested/__init__.na - tests 'from .. import helper'
        (nested_path / "__init__.na").write_text("""
# Test parent imports
from .. import helper as parent_helper
from . import deep

I_AM = "test_pkg.nested"
""")

        # test_pkg/nested/deep.na - tests 'from ... import' (if supported)
        (nested_path / "deep.na").write_text("""
# Deep nested module
from .. import helper as nested_helper

I_AM = "test_pkg.nested.deep"

def deep_function():
    return "Deep function"
""")

    def test_from_dot_import_submodule(self):
        """Test 'from . import submod' in package __init__.na."""
        result = self.sandbox.execute_string("import test_pkg")

        assert result.success is True

        # Test that submod was imported by the package
        submod_result = self.sandbox.execute_string("test_pkg.submod.I_AM")
        assert submod_result.success is True
        assert submod_result.result == "test_pkg.submod"

    def test_from_dot_import_multiple_submodules(self):
        """Test importing multiple submodules from current package."""
        result = self.sandbox.execute_string("import test_pkg")

        assert result.success is True

        # Test both submodules are available
        submod_result = self.sandbox.execute_string("test_pkg.submod.submod_function()")
        helper_result = self.sandbox.execute_string("test_pkg.helper.helper_function()")

        assert submod_result.success is True
        assert helper_result.success is True
        assert "Hello from submod" in str(submod_result.result)
        assert "Helper function" in str(helper_result.result)

    def test_from_dotdot_import_parent(self):
        """Test 'from .. import parent_module' in nested package."""
        result = self.sandbox.execute_string("import test_pkg.nested")

        assert result.success is True

        # Test that parent_helper is available in nested package
        helper_result = self.sandbox.execute_string("test_pkg.nested.parent_helper.helper_function()")
        assert helper_result.success is True
        assert "Helper function" in str(helper_result.result)

    def test_nested_relative_imports(self):
        """Test multiple levels of relative imports."""
        result = self.sandbox.execute_string("import test_pkg.nested.deep")

        assert result.success is True

        # Test that nested_helper (from parent) is available
        helper_result = self.sandbox.execute_string("test_pkg.nested.deep.nested_helper.helper_function()")
        assert helper_result.success is True
        assert "Helper function" in str(helper_result.result)

    def test_direct_from_import_relative(self):
        """Test direct from-import with relative paths."""
        # This should work: importing a function from a submodule
        result = self.sandbox.execute_string("from test_pkg.submod import submod_function")

        assert result.success is True

        # Test direct function access
        func_result = self.sandbox.execute_string("submod_function()")
        assert func_result.success is True
        assert "Hello from submod" in str(func_result.result)

    def test_relative_import_error_handling(self):
        """Test error handling for invalid relative imports."""
        # Test importing non-existent submodule
        result = self.sandbox.execute_string("from test_pkg import nonexistent")

        assert result.success is False
        assert "cannot import name" in str(result.error).lower()

    def test_complex_package_hierarchy_access(self):
        """Test accessing deeply nested modules through relative imports."""
        result = self.sandbox.execute_string("import test_pkg")

        assert result.success is True

        # Test accessing nested module through package
        nested_result = self.sandbox.execute_string("test_pkg.nested.I_AM")
        deep_result = self.sandbox.execute_string("test_pkg.nested.deep.I_AM")

        assert nested_result.success is True
        assert deep_result.success is True
        assert nested_result.result == "test_pkg.nested"
        assert deep_result.result == "test_pkg.nested.deep"

    def teardown_method(self):
        """Clean up test modules and environment."""
        import shutil

        test_modules_path = Path(__file__).parent / "test_modules_relative"
        if test_modules_path.exists():
            shutil.rmtree(test_modules_path)

        # Clean up DANAPATH
        if self.test_modules_path in os.environ.get("DANAPATH", ""):
            os.environ["DANAPATH"] = (
                os.environ["DANAPATH"].replace(f"{self.test_modules_path}{os.pathsep}", "").replace(self.test_modules_path, "")
            )

        # Reset module system
        from dana.__init__ import initialize_module_system, reset_module_system

        reset_module_system()
        initialize_module_system()
