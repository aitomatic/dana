import os

from dana.core.lang import DanaSandbox


class TestComponentImports:
    """Test 2-component submodule imports with comma-separated syntax."""

    def setup_method(self):
        """Set up test fixtures with proper DANAPATH."""
        # Clear module registry to ensure test isolation
        from dana.core.runtime.modules.core import reset_module_system

        reset_module_system()

        # Get the path to test_modules directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_modules_path = os.path.join(current_dir, "test_modules")

        # Set up DANAPATH to include test_modules
        self.original_danapath = os.environ.get("DANAPATH", "")
        os.environ["DANAPATH"] = f"{test_modules_path}:{self.original_danapath}"

        self.sandbox = DanaSandbox()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original DANAPATH
        if self.original_danapath:
            os.environ["DANAPATH"] = self.original_danapath
        else:
            os.environ.pop("DANAPATH", None)

    def test_1_component_import_basic(self):
        """Test basic 1-component import: from simple_math import add"""
        result = self.sandbox.execute_string("from simple_math import add")
        assert result.success, f"1-component import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("add(2, 3)")
        assert func_result.success
        assert func_result.result == 5

    def test_1_component_import_with_alias(self):
        """Test 1-component import with alias: from simple_math import add as addition"""
        result = self.sandbox.execute_string("from simple_math import add as addition")
        assert result.success, f"1-component import with alias failed: {result.error}"

        # Test the aliased function
        func_result = self.sandbox.execute_string("addition(4, 5)")
        assert func_result.success
        assert func_result.result == 9

    def test_1_component_comma_separated_imports(self):
        """Test 1-component comma-separated imports: from simple_math import add, multiply"""
        result = self.sandbox.execute_string("from simple_math import add, multiply")
        assert result.success, f"1-component comma-separated import failed: {result.error}"

        # Test both imported functions
        add_result = self.sandbox.execute_string("add(2, 3)")
        assert add_result.success
        assert add_result.result == 5

        mult_result = self.sandbox.execute_string("multiply(4, 5)")
        assert mult_result.success
        assert mult_result.result == 20

    def test_2_component_import_basic(self):
        """Test basic 2-component import: from a.b import nested_dana_function"""
        result = self.sandbox.execute_string("from a.b import nested_dana_function")
        assert result.success, f"2-component import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("nested_dana_function()")
        assert func_result.success
        assert func_result.result == "Hello from nested Dana module!"

    def test_2_component_import_with_alias(self):
        """Test 2-component import with alias: from a.b import nested_dana_function as ndf"""
        result = self.sandbox.execute_string("from a.b import nested_dana_function as ndf")
        assert result.success, f"2-component import with alias failed: {result.error}"

        # Test the aliased function
        func_result = self.sandbox.execute_string("ndf()")
        assert func_result.success
        assert func_result.result == "Hello from nested Dana module!"

    def test_2_component_import_constant(self):
        """Test 2-component import of constant: from a.b import NESTED_CONSTANT"""
        result = self.sandbox.execute_string("from a.b import NESTED_CONSTANT")
        assert result.success, f"2-component constant import failed: {result.error}"

        # Test the imported constant
        const_result = self.sandbox.execute_string("NESTED_CONSTANT")
        assert const_result.success
        assert const_result.result == "Nested Dana constant"

    def test_2_component_comma_separated_imports(self):
        """Test 2-component comma-separated imports: from a.b import nested_dana_function, NESTED_CONSTANT"""
        result = self.sandbox.execute_string("from a.b import nested_dana_function, NESTED_CONSTANT")
        assert result.success, f"2-component comma-separated import failed: {result.error}"

        # Test both imported items
        func_result = self.sandbox.execute_string("nested_dana_function()")
        assert func_result.success
        assert func_result.result == "Hello from nested Dana module!"

        const_result = self.sandbox.execute_string("NESTED_CONSTANT")
        assert const_result.success
        assert const_result.result == "Nested Dana constant"

    def test_2_component_comma_separated_with_aliases(self):
        """Test 2-component comma-separated imports with aliases: from a.b import nested_dana_function as ndf, NESTED_CONSTANT as NC"""
        result = self.sandbox.execute_string("from a.b import nested_dana_function as ndf, NESTED_CONSTANT as NC")
        assert result.success, f"2-component comma-separated import with aliases failed: {result.error}"

        # Test both aliased items
        func_result = self.sandbox.execute_string("ndf()")
        assert func_result.success
        assert func_result.result == "Hello from nested Dana module!"

        const_result = self.sandbox.execute_string("NC")
        assert const_result.success
        assert const_result.result == "Nested Dana constant"

    def test_2_component_mixed_comma_separated_imports(self):
        """Test 2-component mixed comma-separated imports: from a.b import nested_dana_function, NESTED_CONSTANT as NC"""
        result = self.sandbox.execute_string("from a.b import nested_dana_function, NESTED_CONSTANT as NC")
        assert result.success, f"2-component mixed comma-separated import failed: {result.error}"

        # Test function (not aliased)
        func_result = self.sandbox.execute_string("nested_dana_function()")
        assert func_result.success
        assert func_result.result == "Hello from nested Dana module!"

        # Test constant (aliased)
        const_result = self.sandbox.execute_string("NC")
        assert const_result.success
        assert const_result.result == "Nested Dana constant"

    def test_2_component_deep_function_import(self):
        """Test 2-component import of deep function: from a.b import deep_function"""
        result = self.sandbox.execute_string("from a.b import deep_function")
        assert result.success, f"2-component deep function import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from deep module!"

    def test_2_component_deep_function_comma_separated(self):
        """Test 2-component comma-separated imports with deep function: from a.b import deep_function, DEEP_CONSTANT"""
        result = self.sandbox.execute_string("from a.b import deep_function, DEEP_CONSTANT")
        assert result.success, f"2-component deep function comma-separated import failed: {result.error}"

        # Test both imported items
        func_result = self.sandbox.execute_string("deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from deep module!"

        const_result = self.sandbox.execute_string("DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Deep level constant"

    def test_2_component_mixed_deep_imports(self):
        """Test 2-component mixed imports: from a.b import nested_dana_function, deep_function as df, DEEP_CONSTANT"""
        result = self.sandbox.execute_string("from a.b import nested_dana_function, deep_function as df, DEEP_CONSTANT")
        assert result.success, f"2-component mixed deep imports failed: {result.error}"

        # Test all imported items
        func1_result = self.sandbox.execute_string("nested_dana_function()")
        assert func1_result.success
        assert func1_result.result == "Hello from nested Dana module!"

        func2_result = self.sandbox.execute_string("df()")
        assert func2_result.success
        assert func2_result.result == "Hello from deep module!"

        const_result = self.sandbox.execute_string("DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Deep level constant"

    def test_3_component_import_now_supported(self):
        """Test that 3-component imports are now supported: from a.b.c import deep_function"""
        result = self.sandbox.execute_string("from a.b.c import deep_function")
        assert result.success, f"3-component imports should now be supported: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from deep module!"

    def test_3_component_comma_separated_now_supported(self):
        """Test that 3-component comma-separated imports are now supported: from a.b.c import deep_function, DEEP_CONSTANT"""
        result = self.sandbox.execute_string("from a.b.c import deep_function, DEEP_CONSTANT")
        assert result.success, f"3-component comma-separated imports should now be supported: {result.error}"

        # Test both imported items
        func_result = self.sandbox.execute_string("deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from deep module!"

        const_result = self.sandbox.execute_string("DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Deep level constant"

    def test_3_component_import_with_aliases(self):
        """Test 3-component imports with aliases: from a.b.c import deep_function as df, DEEP_CONSTANT as DC"""
        result = self.sandbox.execute_string("from a.b.c import deep_function as df, DEEP_CONSTANT as DC")
        assert result.success, f"3-component imports with aliases failed: {result.error}"

        # Test both aliased items
        func_result = self.sandbox.execute_string("df()")
        assert func_result.success
        assert func_result.result == "Hello from deep module!"

        const_result = self.sandbox.execute_string("DC")
        assert const_result.success
        assert const_result.result == "Deep level constant"

    def test_3_component_mixed_comma_separated_imports(self):
        """Test 3-component mixed comma-separated imports: from a.b.c import deep_function, DEEP_CONSTANT as DC"""
        result = self.sandbox.execute_string("from a.b.c import deep_function, DEEP_CONSTANT as DC")
        assert result.success, f"3-component mixed comma-separated imports failed: {result.error}"

        # Test function (not aliased) and constant (aliased)
        func_result = self.sandbox.execute_string("deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from deep module!"

        const_result = self.sandbox.execute_string("DC")
        assert const_result.success
        assert const_result.result == "Deep level constant"

    def test_working_utils_package_2_component(self):
        """Test working 2-component imports from utils package: from utils.text import capitalize_words"""
        result = self.sandbox.execute_string("from utils.text import capitalize_words")
        assert result.success, f"utils.text import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string('capitalize_words("hello world")')
        assert func_result.success
        assert func_result.result == "Hello World"

    def test_working_utils_package_comma_separated(self):
        """Test working comma-separated imports from utils package: from utils.text import capitalize_words, title_case"""
        result = self.sandbox.execute_string("from utils.text import capitalize_words, title_case")
        assert result.success, f"utils.text comma-separated import failed: {result.error}"

        # Test both imported functions
        func1_result = self.sandbox.execute_string('capitalize_words("hello world")')
        assert func1_result.success
        assert func1_result.result == "Hello World"

        func2_result = self.sandbox.execute_string('title_case("hello world")')
        assert func2_result.success
        assert func2_result.result == "Hello World"
