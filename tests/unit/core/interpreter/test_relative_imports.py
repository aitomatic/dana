"""
Tests for relative import functionality in Dana.

This module tests the dot-prefix relative import feature:
- from .module import name (same package)
- from ..module import name (parent package)
- from ...module import name (grandparent package)
- Arbitrary depth relative imports

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.runtime.modules.core import initialize_module_system, reset_module_system


class TestRelativeImports:
    """Test class for relative import functionality."""

    def setup_method(self):
        """Reset module system before each test."""
        reset_module_system()

    def teardown_method(self):
        """Reset module system after each test."""
        reset_module_system()

    def test_same_package_relative_import(self, tmp_path):
        """Test relative import from same package (.module)."""
        # Create package structure
        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()

        # Create __init__.na
        init_file = pkg_dir / "__init__.na"
        init_file.write_text("# Package init")

        # Create utility module
        util_file = pkg_dir / "utils.na"
        util_file.write_text("""
def get_message() -> str:
    return "Hello from utils"
""")

        # Create package __init__.na that imports from same package
        pkg_init = pkg_dir / "__init__.na"
        pkg_init.write_text("""
from .utils import get_message

package_result = get_message()
""")

        # Create driver module that imports the package
        driver_file = tmp_path / "driver.na"
        driver_file.write_text("""
import mypackage

result = mypackage.package_result
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.quick_run(driver_file)

        assert result.success
        assert result.final_context.get("local:result") == "Hello from utils"

    def test_parent_package_relative_import(self, tmp_path):
        """Test relative import from parent package (..module)."""
        # Create package structure
        parent_dir = tmp_path / "parent"
        parent_dir.mkdir()

        # Create parent package __init__.na
        parent_init = parent_dir / "__init__.na"
        parent_init.write_text('parent_message = "Hello from parent"')

        # Create parent module
        parent_module = parent_dir / "shared.na"
        parent_module.write_text("""
def get_shared_value() -> str:
    return "Shared value"
""")

        # Create subpackage
        sub_dir = parent_dir / "sub"
        sub_dir.mkdir()

        # Create subpackage __init__.na that imports from parent
        sub_init = sub_dir / "__init__.na"
        sub_init.write_text("""
from ..shared import get_shared_value
from .. import parent_message

sub_result = f"{parent_message}: {get_shared_value()}"
""")

        # Create driver module to import the subpackage
        driver_file = tmp_path / "driver.na"
        driver_file.write_text("""
import parent.sub

result = parent.sub.sub_result
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.quick_run(driver_file)

        assert result.success
        result_value = str(result.final_context.get("local:result"))
        assert "Hello from parent:" in result_value and "Shared value" in result_value

    def test_grandparent_package_relative_import(self, tmp_path):
        """Test relative import from grandparent package (...module)."""
        # Create package structure: grandparent/parent/sub
        grandparent_dir = tmp_path / "grandparent"
        grandparent_dir.mkdir()

        # Create grandparent __init__.na
        grandparent_init = grandparent_dir / "__init__.na"
        grandparent_init.write_text('top_level = "Top level message"')

        # Create parent package
        parent_dir = grandparent_dir / "parent"
        parent_dir.mkdir()

        # Create parent __init__.na
        parent_init = parent_dir / "__init__.na"
        parent_init.write_text("# Parent package")

        # Create subpackage
        sub_dir = parent_dir / "sub"
        sub_dir.mkdir()

        # Create subpackage __init__.na that imports from grandparent
        sub_init = sub_dir / "__init__.na"
        sub_init.write_text("""
from ... import top_level

sub_result = f"Deep: {top_level}"
""")

        # Create driver module to import the deep subpackage
        driver_file = tmp_path / "driver.na"
        driver_file.write_text("""
import grandparent.parent.sub

result = grandparent.parent.sub.sub_result
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.quick_run(driver_file)

        assert result.success
        result_value = str(result.final_context.get("local:result"))
        assert "Deep:" in result_value and "Top level message" in result_value

    def test_mixed_relative_imports(self, tmp_path):
        """Test mixing different levels of relative imports."""
        # Create package structure
        pkg_dir = tmp_path / "mixed"
        pkg_dir.mkdir()

        # Create package __init__.na
        pkg_init = pkg_dir / "__init__.na"
        pkg_init.write_text('pkg_name = "Mixed Package"')

        # Create package-level module
        pkg_module = pkg_dir / "config.na"
        pkg_module.write_text("""
default_setting = "production"
""")

        # Create subpackage
        sub_dir = pkg_dir / "components"
        sub_dir.mkdir()

        # Create subpackage __init__.na
        sub_init = sub_dir / "__init__.na"
        sub_init.write_text('sub_name = "Components"')

        # Create module in subpackage
        sub_module = sub_dir / "helper.na"
        sub_module.write_text("""
helper_value = 42
""")

        # Create processor module that uses mixed relative imports
        processor_module = sub_dir / "processor.na"
        processor_module.write_text("""
# Import from parent package  
from .. import pkg_name
from ..config import default_setting

# Import from same package
from . import sub_name
from .helper import helper_value

result = f"{pkg_name} - {sub_name}: {default_setting}, {helper_value}"
""")

        # Create driver module in the tmp_path directory
        driver_file = tmp_path / "driver.na"
        driver_file.write_text("""
import mixed.components.processor

result = mixed.components.processor.result
""")

        # Initialize module system with tmp_path so it can find the package
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.quick_run(driver_file)

        # Check if the failure is due to module not found
        if not result.success:
            print(f"Error: {result.error}")

        assert result.success
        expected = "Mixed Package - Components: production, 42"
        assert result.final_context.get("local:result") == expected

    def test_relative_import_error_handling(self, tmp_path):
        """Test error handling for invalid relative imports."""
        # Create simple package
        pkg_dir = tmp_path / "simple"
        pkg_dir.mkdir()

        # Create package __init__.na
        pkg_init = pkg_dir / "__init__.na"
        pkg_init.write_text("# Simple package")

        # Create module that tries to go beyond top-level in the package
        module_file = pkg_dir / "bad_import.na"
        module_file.write_text("""
# This should fail - trying to go beyond top-level package when loaded
from ...nonexistent import something

result = "should not reach here"
""")

        # Create driver module in tmp_path directory to test error handling
        driver_file = tmp_path / "driver.na"
        driver_file.write_text("""
# This should fail when trying to import the bad module
import simple.bad_import
result = simple.bad_import.result
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module - should fail with the relative import error
        result = DanaSandbox.quick_run(driver_file)

        # Should fail with the relative import error
        assert not result.success
        assert result.error is not None
        error_message = str(result.error)
        assert "beyond top-level package" in error_message

    def test_relative_import_with_alias(self, tmp_path):
        """Test relative imports with aliases."""
        # Create package
        pkg_dir = tmp_path / "aliased"
        pkg_dir.mkdir()

        # Create package __init__.na
        pkg_init = pkg_dir / "__init__.na"
        pkg_init.write_text("# Aliased package")

        # Create module
        module_file = pkg_dir / "data.na"
        module_file.write_text("""
def process() -> str:
    return "processed"
""")

        # Create main module with aliased relative import
        main_file = pkg_dir / "__init__.na"
        main_file.write_text("""
from .data import process as proc

result = proc()
""")

        # Create driver module
        driver_file = tmp_path / "driver.na"
        driver_file.write_text("""
import aliased

result = aliased.result
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Run driver module
        result = DanaSandbox.quick_run(driver_file)

        assert result.success
        assert result.final_context.get("local:result") == "processed"

    def test_relative_import_from_eval_context(self, tmp_path):
        """Test that relative imports fail gracefully in eval context."""
        # Create package
        pkg_dir = tmp_path / "eval_test"
        pkg_dir.mkdir()

        # Create package __init__.na
        pkg_init = pkg_dir / "__init__.na"
        pkg_init.write_text("# Eval test package")

        # Create module
        module_file = pkg_dir / "utility.na"
        module_file.write_text("""
value = "utility value"
""")

        # Initialize module system
        initialize_module_system([str(tmp_path)])

        # Create sandbox
        sandbox = DanaSandbox()

        # Try to use relative import - this should fail since no file context
        relative_result = sandbox.eval("from .utility import value")
        assert not relative_result.success
        assert "without package context" in str(relative_result.error)
