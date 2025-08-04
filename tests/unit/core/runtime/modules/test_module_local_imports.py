"""
Test module-local imports feature.

This test ensures that Dana modules can import siblings directly without
relative import syntax, making imports more intuitive and portable.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.runtime.modules.core import initialize_module_system, reset_module_system


class TestModuleLocalImports:
    """Test module-local import functionality."""

    def setup_method(self):
        """Reset module system before each test."""
        reset_module_system()

    def teardown_method(self):
        """Reset module system after each test."""
        reset_module_system()

    def test_sibling_import(self, tmp_path):
        """Test that modules can import siblings in the same directory."""
        # Create test modules
        math_module = tmp_path / "math_utils.na"
        math_module.write_text("""
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b
""")

        main_module = tmp_path / "main.na"
        main_module.write_text("""
# Import sibling module directly without relative syntax
import math_utils

result1 = math_utils.add(5, 3)
result2 = math_utils.multiply(4, 7)
""")

        # Initialize module system
        initialize_module_system()

        # Run main module
        result = DanaSandbox.execute_file_once(main_module)

        assert result.success
        assert result.final_context.get("local:result1") == 8
        assert result.final_context.get("local:result2") == 28

    def test_from_import_sibling(self, tmp_path):
        """Test from-import for sibling modules."""
        # Create test modules
        utils_module = tmp_path / "string_utils.na"
        utils_module.write_text("""
def capitalize_words(text: str) -> str:
    words = text.split()
    capitalized = []
    for word in words:
        capitalized.append(word.capitalize())
    return " ".join(capitalized)

def reverse_string(text: str) -> str:
    return text[::-1]
""")

        main_module = tmp_path / "processor.na"
        main_module.write_text("""
# From-import sibling module
from string_utils import capitalize_words, reverse_string

text = "hello world"
capitalized = capitalize_words(text)
reversed_text = reverse_string(text)
""")

        # Initialize module system
        initialize_module_system()

        # Run main module
        result = DanaSandbox.execute_file_once(main_module)

        assert result.success
        assert result.final_context.get("local:capitalized") == "Hello World"
        assert result.final_context.get("local:reversed_text") == "dlrow olleh"

    def test_nested_directory_imports(self, tmp_path):
        """Test imports from modules in nested directories."""
        # Create nested structure
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()

        # Create __init__.na to make lib a package
        lib_init = lib_dir / "__init__.na"
        lib_init.write_text("# lib package")

        # Create library module
        lib_module = lib_dir / "helper.na"
        lib_module.write_text("""
def greet(name: str) -> str:
    return f"Hello, {name}!"
""")

        # Create utils in main directory
        utils_module = tmp_path / "utils.na"
        utils_module.write_text("""
# Import from subdirectory
import lib.helper

def welcome(name: str) -> str:
    return lib.helper.greet(name) + " Welcome aboard!"
""")

        # Create main module
        main_module = tmp_path / "app.na"
        main_module.write_text("""
# Import local module that imports from subdirectory
import utils

message = utils.welcome("Alice")
""")

        # Initialize module system with tmp_path so lib package is found
        initialize_module_system([str(tmp_path)])

        # Run main module
        result = DanaSandbox.execute_file_once(main_module)

        assert result.success
        assert result.final_context.get("local:message") == "Hello, Alice! Welcome aboard!"

    def test_chained_sibling_imports(self, tmp_path):
        """Test chain of sibling imports (A imports B, B imports C)."""
        # Create module C
        module_c = tmp_path / "constants.na"
        module_c.write_text("""
PI = 3.14159
E = 2.71828
""")

        # Create module B that imports C
        module_b = tmp_path / "calculations.na"
        module_b.write_text("""
import constants

def circle_area(radius: float) -> float:
    return constants.PI * radius * radius
""")

        # Create module A that imports B
        module_a = tmp_path / "geometry.na"
        module_a.write_text("""
import calculations

area = calculations.circle_area(5.0)
""")

        # Initialize module system
        initialize_module_system()

        # Run module A
        result = DanaSandbox.execute_file_once(module_a)

        assert result.success
        expected_area = 3.14159 * 5.0 * 5.0
        assert abs(result.final_context.get("local:area") - expected_area) < 0.0001

    def test_import_precedence(self, tmp_path):
        """Test that local imports take precedence over search path imports."""
        # Create a module in the standard search path
        standard_dir = tmp_path / "standard"
        standard_dir.mkdir()

        standard_module = standard_dir / "config.na"
        standard_module.write_text("""
setting = "standard"
""")

        # Create a local module with the same name
        local_dir = tmp_path / "local"
        local_dir.mkdir()

        local_module = local_dir / "config.na"
        local_module.write_text("""
setting = "local"
""")

        # Create main module in local directory
        main_module = local_dir / "main.na"
        main_module.write_text("""
import config
value = config.setting
""")

        # Initialize with standard dir in search path
        initialize_module_system([str(standard_dir)])

        # Run main module - should find local config first
        result = DanaSandbox.execute_file_once(main_module)

        assert result.success
        assert result.final_context.get("local:value") == "local"

    def test_mixed_import_styles(self, tmp_path):
        """Test mixing local imports with absolute imports."""
        # Create package structure
        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()

        # Create package __init__.na
        init_file = pkg_dir / "__init__.na"
        init_file.write_text("""
package_name = "mypackage"
""")

        # Create package module
        pkg_module = pkg_dir / "data.na"
        pkg_module.write_text("""
data_value = 42
""")

        # Create local helper
        helper_module = tmp_path / "helper.na"
        helper_module.write_text("""
helper_value = 100
""")

        # Create main module
        main_module = tmp_path / "main.na"
        main_module.write_text("""
# Mix of import styles
import helper  # Local sibling import
import mypackage.data  # Package import

total = helper.helper_value + mypackage.data.data_value
""")

        # Initialize with tmp_path in search path for package imports
        initialize_module_system([str(tmp_path)])

        # Run main module
        result = DanaSandbox.execute_file_once(main_module)

        assert result.success
        assert result.final_context.get("local:total") == 142

    def test_import_from_different_directories(self, tmp_path):
        """Test that modules in different directories maintain their own import context."""
        # Create two separate directories
        dir1 = tmp_path / "project1"
        dir1.mkdir()

        dir2 = tmp_path / "project2"
        dir2.mkdir()

        # Create config in each directory with different values
        config1 = dir1 / "config.na"
        config1.write_text("""
name = "Project 1"
value = 10
""")

        config2 = dir2 / "config.na"
        config2.write_text("""
name = "Project 2"
value = 20
""")

        # Create main modules that import their local config
        main1 = dir1 / "main.na"
        main1.write_text("""
import config
project_info = config.name + " - " + str(config.value)
""")

        main2 = dir2 / "main.na"
        main2.write_text("""
import config
project_info = config.name + " - " + str(config.value)
""")

        # Run first module
        reset_module_system()
        initialize_module_system()
        result1 = DanaSandbox.execute_file_once(main1)

        # Reset and run second module
        reset_module_system()
        initialize_module_system()
        result2 = DanaSandbox.execute_file_once(main2)

        assert result1.success
        assert result2.success
        assert result1.final_context.get("local:project_info") == "Project 1 - 10"
        assert result2.final_context.get("local:project_info") == "Project 2 - 20"

    def test_no_file_context_fallback(self, tmp_path):
        """Test that imports still work when no file context is available (e.g., eval)."""
        # Create a module in the standard search path
        module_file = tmp_path / "standard_module.na"
        module_file.write_text("""
standard_value = "available"
""")

        # Evaluate code without file context, passing the search path directly
        code = """
import standard_module
result = standard_module.standard_value
"""

        result = DanaSandbox.execute_string_once(code, module_search_paths=[str(tmp_path)])

        assert result.success
        assert result.final_context.get("local:result") == "available"

    def test_import_with_alias(self, tmp_path):
        """Test that aliased imports work with local modules."""
        # Create module
        long_module = tmp_path / "very_long_module_name.na"
        long_module.write_text("""
def process(x: int) -> int:
    return x * 2
""")

        # Create main module with aliased import
        main_module = tmp_path / "main.na"
        main_module.write_text("""
import very_long_module_name as vlm

result = vlm.process(21)
""")

        # Initialize module system
        initialize_module_system()

        # Run main module
        result = DanaSandbox.execute_file_once(main_module)

        assert result.success
        assert result.final_context.get("local:result") == 42

    def test_error_handling(self, tmp_path):
        """Test proper error messages for failed local imports."""
        # Create main module that tries to import non-existent module
        main_module = tmp_path / "main.na"
        main_module.write_text("""
import nonexistent_module
""")

        # Initialize module system
        initialize_module_system()

        # Run main module
        result = DanaSandbox.execute_file_once(main_module)

        assert not result.success
        assert "nonexistent_module" in str(result.error)
        assert "not found" in str(result.error)
