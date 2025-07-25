#!/usr/bin/env python3

import os

from dana.core.lang import DanaSandbox
from dana.core.runtime.modules.core import initialize_module_system, reset_module_system


class TestUnderscorePrivacy:
    """Test class for underscore privacy in Dana imports."""

    def setup_method(self):
        """Set up test fixtures with proper DANAPATH."""
        # Clear struct registry to ensure test isolation
        from dana.core.lang.interpreter.struct_system import StructTypeRegistry

        StructTypeRegistry.clear()

        # Get the path to test_modules directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_modules_path = os.path.join(current_dir, "test_modules")

        # Set up DANAPATH to include test_modules
        self.original_danapath = os.environ.get("DANAPATH", "")
        os.environ["DANAPATH"] = f"{test_modules_path}:{self.original_danapath}"

        # Reset and reinitialize the module system to pick up the updated search paths
        reset_module_system()
        initialize_module_system()

        self.sandbox = DanaSandbox()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original DANAPATH
        os.environ["DANAPATH"] = self.original_danapath
        self.sandbox._cleanup()

    def test_public_function_import_succeeds(self):
        """Test that public functions (no underscore) can be imported."""
        result = self.sandbox.eval("from privacy_test import public_function")
        assert result.success, f"Failed to import public function: {result.error}"

        # Test the function can be called
        call_result = self.sandbox.eval("public_function()")
        assert call_result.success, f"Failed to call imported function: {call_result.error}"
        assert call_result.result == "This is a public function"

    def test_public_constant_import_succeeds(self):
        """Test that public constants (no underscore) can be imported."""
        result = self.sandbox.eval("from privacy_test import PUBLIC_CONSTANT")
        assert result.success, f"Failed to import public constant: {result.error}"

        # Test the constant value
        value_result = self.sandbox.eval("PUBLIC_CONSTANT")
        assert value_result.success, f"Failed to access imported constant: {value_result.error}"
        assert value_result.result == "This is a public constant"

    def test_private_function_import_fails(self):
        """Test that private functions (underscore prefix) cannot be imported."""
        result = self.sandbox.eval("from privacy_test import _private_function")
        assert not result.success, "Private function import should fail"
        assert "names starting with '_' are private" in str(result.error)

    def test_private_constant_import_fails(self):
        """Test that private constants (underscore prefix) cannot be imported."""
        result = self.sandbox.eval("from privacy_test import _PRIVATE_CONSTANT")
        assert not result.success, "Private constant import should fail"
        assert "names starting with '_' are private" in str(result.error)

    def test_private_struct_import_fails(self):
        """Test that private structs (underscore prefix) cannot be imported."""
        result = self.sandbox.eval("from privacy_test import _PrivateStruct")
        assert not result.success, "Private struct import should fail"
        assert "names starting with '_' are private" in str(result.error)

    def test_helper_function_import_fails(self):
        """Test that helper functions (underscore prefix) cannot be imported."""
        result = self.sandbox.eval("from privacy_test import _helper_function")
        assert not result.success, "Helper function import should fail"
        assert "names starting with '_' are private" in str(result.error)

    def test_public_function_can_use_private_internally(self):
        """Test that public functions can use private functions internally."""
        result = self.sandbox.eval("from privacy_test import get_public_data")
        assert result.success, f"Failed to import public function: {result.error}"

        # Test the function can be called and uses private function internally
        call_result = self.sandbox.eval("get_public_data()")
        assert call_result.success, f"Failed to call function that uses private helper: {call_result.error}"
        assert "Public data with Internal helper function" in call_result.result

    def test_multiple_public_imports_succeed(self):
        """Test importing multiple public names in one statement."""
        result = self.sandbox.eval("from privacy_test import public_function, PUBLIC_CONSTANT, describe_module")
        assert result.success, f"Failed to import multiple public names: {result.error}"

        # Test all imports work
        func_result = self.sandbox.eval("public_function()")
        assert func_result.success and func_result.result == "This is a public function"

        const_result = self.sandbox.eval("PUBLIC_CONSTANT")
        assert const_result.success and const_result.result == "This is a public constant"

        desc_result = self.sandbox.eval("describe_module()")
        assert desc_result.success and "Privacy test module" in desc_result.result

    def test_mixed_public_private_import_fails(self):
        """Test that importing mixed public/private names fails on the private ones."""
        # This should fail because _private_function is private
        result = self.sandbox.eval("from privacy_test import public_function, _private_function")
        assert not result.success, "Mixed public/private import should fail"
        assert "names starting with '_' are private" in str(result.error)

    def test_module_level_import_still_works(self):
        """Test that module-level imports still work (doesn't affect module import, only from imports)."""
        result = self.sandbox.eval("import privacy_test")
        assert result.success, f"Module-level import should work: {result.error}"

        # We can access the module but not private attributes directly through from import
        module_result = self.sandbox.eval("privacy_test")
        assert module_result.success, "Should be able to access imported module"

    def test_struct_import_now_works(self):
        """Test that public structs can now be imported (this was broken before)."""
        result = self.sandbox.eval("from privacy_test import PublicStruct")
        assert result.success, f"Failed to import public struct: {result.error}"

        # Verify struct can be used
        # Note: We can't test struct instantiation here since we don't know the exact syntax,
        # but the import should succeed
        struct_result = self.sandbox.eval("PublicStruct")
        assert struct_result.success, "Should be able to access imported struct"
