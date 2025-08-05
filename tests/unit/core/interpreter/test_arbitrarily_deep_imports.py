#!/usr/bin/env python3

import os

from dana.core.lang import DanaSandbox


class TestArbitrarilyDeepImports:
    """Test class for arbitrarily deep Dana module imports."""

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

    def test_4_component_import_verification(self):
        """Verify 4-component imports work: from a.b.c.d import very_deep_function"""
        result = self.sandbox.execute_string("from a.b.c.d import very_deep_function")
        assert result.success, f"4-component import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("very_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from very deep module!"

    def test_5_component_import_basic(self):
        """Test 5-component imports: from a.b.c.d.e import module_function"""
        # First check if the module can be directly imported
        import_result = self.sandbox.execute_string("import a.b.c.d.e")
        assert import_result.success, f"5-component module import failed: {import_result.error}"

    def test_6_component_import_basic(self):
        """Test 6-component imports: from a.b.c.d.e.f import extremely_deep_function"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f import extremely_deep_function")
        assert result.success, f"6-component import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("extremely_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from extremely deep module!"

    def test_6_component_import_constant(self):
        """Test 6-component import of constant: from a.b.c.d.e.f import EXTREMELY_DEEP_CONSTANT"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f import EXTREMELY_DEEP_CONSTANT")
        assert result.success, f"6-component constant import failed: {result.error}"

        # Test the imported constant
        const_result = self.sandbox.execute_string("EXTREMELY_DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Extremely deep level constant"

    def test_6_component_comma_separated_imports(self):
        """Test 6-component comma-separated imports: from a.b.c.d.e.f import extremely_deep_function, EXTREMELY_DEEP_CONSTANT"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f import extremely_deep_function, EXTREMELY_DEEP_CONSTANT")
        assert result.success, f"6-component comma-separated import failed: {result.error}"

        # Test both imported items
        func_result = self.sandbox.execute_string("extremely_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from extremely deep module!"

        const_result = self.sandbox.execute_string("EXTREMELY_DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Extremely deep level constant"

    def test_6_component_import_with_alias(self):
        """Test 6-component import with alias: from a.b.c.d.e.f import extremely_deep_function as edf"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f import extremely_deep_function as edf")
        assert result.success, f"6-component import with alias failed: {result.error}"

        # Test the aliased function
        func_result = self.sandbox.execute_string("edf()")
        assert func_result.success
        assert func_result.result == "Hello from extremely deep module!"

    def test_6_component_mixed_comma_imports(self):
        """Test 6-component mixed comma-separated imports with aliases"""
        result = self.sandbox.execute_string(
            "from a.b.c.d.e.f import extremely_deep_function as edf, EXTREMELY_DEEP_CONSTANT, calculate_deep_depth"
        )
        assert result.success, f"6-component mixed comma imports failed: {result.error}"

        # Test all imported items
        func_result = self.sandbox.execute_string("edf()")
        assert func_result.success
        assert func_result.result == "Hello from extremely deep module!"

        const_result = self.sandbox.execute_string("EXTREMELY_DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Extremely deep level constant"

        depth_result = self.sandbox.execute_string("calculate_deep_depth()")
        assert depth_result.success
        assert depth_result.result == 6

    def test_7_component_import_basic(self):
        """Test 7-component imports: from a.b.c.d.e.f.g import ultra_deep_function"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f.g import ultra_deep_function")
        assert result.success, f"7-component import failed: {result.error}"

        # Test the imported function
        func_result = self.sandbox.execute_string("ultra_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from ultra deep module!"

    def test_7_component_import_constant(self):
        """Test 7-component import of constant: from a.b.c.d.e.f.g import ULTRA_DEEP_CONSTANT"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f.g import ULTRA_DEEP_CONSTANT")
        assert result.success, f"7-component constant import failed: {result.error}"

        # Test the imported constant
        const_result = self.sandbox.execute_string("ULTRA_DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Ultra deep level constant"

    def test_7_component_comma_separated_imports(self):
        """Test 7-component comma-separated imports"""
        result = self.sandbox.execute_string("from a.b.c.d.e.f.g import ultra_deep_function, ULTRA_DEEP_CONSTANT, calculate_ultra_depth")
        assert result.success, f"7-component comma-separated import failed: {result.error}"

        # Test all imported items
        func_result = self.sandbox.execute_string("ultra_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from ultra deep module!"

        const_result = self.sandbox.execute_string("ULTRA_DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Ultra deep level constant"

        depth_result = self.sandbox.execute_string("calculate_ultra_depth()")
        assert depth_result.success
        assert depth_result.result == 7

    def test_7_component_import_with_aliases(self):
        """Test 7-component imports with mixed aliases"""
        result = self.sandbox.execute_string(
            "from a.b.c.d.e.f.g import ultra_deep_function as udf, ULTRA_DEEP_CONSTANT as UDC, describe_location"
        )
        assert result.success, f"7-component import with aliases failed: {result.error}"

        # Test all imported items
        func_result = self.sandbox.execute_string("udf()")
        assert func_result.success
        assert func_result.result == "Hello from ultra deep module!"

        const_result = self.sandbox.execute_string("UDC")
        assert const_result.success
        assert const_result.result == "Ultra deep level constant"

        desc_result = self.sandbox.execute_string("describe_location()")
        assert desc_result.success
        assert desc_result.result == "Seven levels deep in the import hierarchy"

    def test_deep_import_module_access(self):
        """Test that deeply imported modules maintain their full namespace access"""
        result = self.sandbox.execute_string("import a.b.c.d.e.f.g")
        assert result.success, f"Deep module import failed: {result.error}"

        # Test accessing through full namespace
        func_result = self.sandbox.execute_string("a.b.c.d.e.f.g.ultra_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from ultra deep module!"

    def test_deep_import_with_alias_access(self):
        """Test deep import with alias for easier access"""
        result = self.sandbox.execute_string("import a.b.c.d.e.f.g as ultra_deep")
        assert result.success, f"Deep import with alias failed: {result.error}"

        # Test accessing through alias
        func_result = self.sandbox.execute_string("ultra_deep.ultra_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from ultra deep module!"

        const_result = self.sandbox.execute_string("ultra_deep.ULTRA_DEEP_CONSTANT")
        assert const_result.success
        assert const_result.result == "Ultra deep level constant"

    def test_mixed_depth_imports_in_same_session(self):
        """Test that imports of different depths work correctly in the same session"""
        # Import from different depths
        results = [
            self.sandbox.execute_string("from simple_math import add"),  # 1 component
            self.sandbox.execute_string("from a.b import nested_dana_function"),  # 2 components
            self.sandbox.execute_string("from a.b.c import deep_function"),  # 3 components
            self.sandbox.execute_string("from a.b.c.d import very_deep_function"),  # 4 components
            self.sandbox.execute_string("from a.b.c.d.e.f import extremely_deep_function"),  # 6 components
            self.sandbox.execute_string("from a.b.c.d.e.f.g import ultra_deep_function"),  # 7 components
        ]

        # All imports should succeed
        for i, result in enumerate(results):
            assert result.success, f"Mixed depth import {i + 1} failed: {result.error}"

        # Test all functions work
        test_calls = [
            ("add(2, 3)", 5),
            ("nested_dana_function()", "Hello from nested Dana module!"),
            ("deep_function()", "Hello from deep module!"),
            ("very_deep_function()", "Hello from very deep module!"),
            ("extremely_deep_function()", "Hello from extremely deep module!"),
            ("ultra_deep_function()", "Hello from ultra deep module!"),
        ]

        for call, expected in test_calls:
            result = self.sandbox.execute_string(call)
            assert result.success, f"Function call '{call}' failed: {result.error}"
            assert result.result == expected, f"Function call '{call}' returned {result.result}, expected {expected}"

    def test_performance_deep_imports(self):
        """Test that deep imports don't cause performance issues"""
        import time

        # Time multiple deep imports
        start_time = time.time()

        for i in range(5):  # Import multiple times to test caching
            result = self.sandbox.execute_string("from a.b.c.d.e.f.g import ultra_deep_function")
            assert result.success, f"Performance test import {i + 1} failed: {result.error}"

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete reasonably quickly (under 2 seconds for 5 imports)
        assert total_time < 2.0, f"Deep imports took too long: {total_time:.2f} seconds"

        # Verify functionality still works
        func_result = self.sandbox.execute_string("ultra_deep_function()")
        assert func_result.success
        assert func_result.result == "Hello from ultra deep module!"
