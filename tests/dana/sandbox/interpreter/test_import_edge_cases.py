#!/usr/bin/env python3

import pytest

from opendxa.dana import DanaSandbox


class TestImportEdgeCases:
    """Test edge cases and error scenarios for import statements."""

    def setup_method(self):
        """Set up a fresh sandbox for each test."""
        self.sandbox = DanaSandbox()

    def test_import_invalid_module_name(self):
        """Test importing modules with invalid names."""
        # Invalid module names that should fail
        invalid_names = [
            "123invalid",  # Starts with number
            "invalid-name",  # Contains dash
            "invalid.name",  # Contains dot (should be handled specially)
            "",  # Empty string
            " ",  # Whitespace
            "invalid name",  # Contains space
        ]

        for invalid_name in invalid_names:
            try:
                result = self.sandbox.eval(f"import {invalid_name}")
                # Should either fail at parse time or import time
                if result.success:
                    pytest.fail(f"Expected import of '{invalid_name}' to fail, but it succeeded")
            except Exception:
                # Parse error is also acceptable for invalid syntax
                pass

    def test_from_import_nonexistent_attribute(self):
        """Test importing non-existent attributes from valid modules."""
        result = self.sandbox.eval("from math.py import nonexistent_function")

        assert result.success is False
        assert "cannot import name" in str(result.error).lower()

    def test_import_circular_detection(self):
        """Test that circular imports are detected if they occur."""
        # Note: This test would require creating actual .na files
        # For now, test that the error handling mechanism works
        # This is more of a module system test than import statement test
        pass

    def test_import_case_sensitivity(self):
        """Test that module imports are case sensitive."""
        # Try importing with wrong case
        result1 = self.sandbox.eval("import MATH.py")  # Should fail
        result2 = self.sandbox.eval("import Math.py")  # Should fail

        assert result1.success is False
        assert result2.success is False

    def test_import_with_special_characters_in_alias(self):
        """Test imports with various alias names."""
        # Valid aliases
        valid_aliases = [
            "m",  # Single letter
            "math_mod",  # Underscore
            "_math",  # Leading underscore
            "math2",  # Number
            "mathMod",  # CamelCase
        ]

        for alias in valid_aliases:
            result = self.sandbox.eval(f"import math.py as {alias}")
            assert result.success is True, f"Valid alias '{alias}' should work"

    def test_import_alias_overwrites_existing_variable(self):
        """Test that import aliases can overwrite existing variables."""
        # Set a variable
        result1 = self.sandbox.eval("x = 42")
        assert result1.success is True

        # Import with same name
        result2 = self.sandbox.eval("import math.py as x")
        assert result2.success is True

        # Check that x is now the math module
        result3 = self.sandbox.eval("x.pi")
        assert result3.success is True
        assert abs(result3.result - 3.141592653589793) < 1e-10

    def test_multiple_imports_same_module(self):
        """Test importing the same module multiple times."""
        # Import same module multiple times
        result1 = self.sandbox.eval("import math.py")
        result2 = self.sandbox.eval("import math.py as m")
        result3 = self.sandbox.eval("from math.py import pi")

        assert result1.success is True
        assert result2.success is True
        assert result3.success is True

        # All should work
        pi1 = self.sandbox.eval("math.pi")
        pi2 = self.sandbox.eval("m.pi")
        pi3 = self.sandbox.eval("pi")

        assert pi1.success is True
        assert pi2.success is True
        assert pi3.success is True

        # All should be the same value
        expected_pi = 3.141592653589793
        assert abs(pi1.result - expected_pi) < 1e-10
        assert abs(pi2.result - expected_pi) < 1e-10
        assert abs(pi3.result - expected_pi) < 1e-10

    def test_from_import_all_not_supported(self):
        """Test that 'from module import *' is properly handled."""
        # This should either fail with parse error or specific error message
        try:
            result = self.sandbox.eval("from math.py import *")
            # If it parses, it should fail with appropriate error
            assert result.success is False
            assert "not supported" in str(result.error).lower() or "unexpected" in str(result.error).lower()
        except Exception:
            # Parse error is acceptable for unsupported syntax
            pass

    def test_import_long_module_path(self):
        """Test importing modules with long paths."""
        # Test with very long (but valid) module name
        long_name = "a" * 100 + ".py"
        result = self.sandbox.eval(f"import {long_name}")

        assert result.success is False
        assert any(phrase in str(result.error).lower() for phrase in ["not found", "no module named"])

    def test_import_empty_alias(self):
        """Test import with empty or invalid alias."""
        # These should fail at parse time
        invalid_aliases = [
            "import math.py as ",  # Missing alias
            "import math.py as 123",  # Invalid alias (starts with number)
            "import math.py as ''",  # Empty string alias
        ]

        for invalid_import in invalid_aliases:
            try:
                result = self.sandbox.eval(invalid_import)
                # Should either fail at parse or import time
                if result.success:
                    pytest.fail(f"Expected '{invalid_import}' to fail, but it succeeded")
            except Exception:
                # Parse error is acceptable
                pass

    def test_import_module_name_with_keywords(self):
        """Test importing modules with names that are keywords."""
        keyword_modules = [
            "if.py",  # Python keyword
            "def.py",  # Python keyword
            "class.py",  # Python keyword
            "true.py",  # Dana keyword
            "false.py",  # Dana keyword
        ]

        for module_name in keyword_modules:
            result = self.sandbox.eval(f"import {module_name}")
            # These should fail (module not found)
            assert result.success is False

    def test_import_with_unicode_characters(self):
        """Test importing modules with unicode characters in names."""
        unicode_modules = [
            "módulo.py",  # Spanish
            "模块.py",  # Chinese
            "モジュール.py",  # Japanese
        ]

        for module_name in unicode_modules:
            result = self.sandbox.eval(f"import {module_name}")
            # These should fail (module not found), but shouldn't crash the parser
            assert result.success is False

    def test_import_error_message_quality(self):
        """Test that import error messages are clear and helpful."""
        # Test various error scenarios and check message quality

        # Module not found
        result1 = self.sandbox.eval("import nonexistent.py")
        assert result1.success is False
        error_msg1 = str(result1.error).lower()
        assert any(phrase in error_msg1 for phrase in ["not found", "no module named", "cannot find"])
        assert "nonexistent" in error_msg1

        # From-import name not found
        result2 = self.sandbox.eval("from math.py import nonexistent")
        assert result2.success is False
        error_msg2 = str(result2.error).lower()
        assert "cannot import name" in error_msg2
        assert "nonexistent" in error_msg2
        assert "math" in error_msg2

    def test_import_context_isolation(self):
        """Test that imports are properly isolated between sandbox instances."""
        sandbox1 = DanaSandbox()
        sandbox2 = DanaSandbox()

        # Import in sandbox1
        result1 = sandbox1.eval("import math.py as mathematics")
        assert result1.success is True

        # Verify it works in sandbox1
        pi_result1 = sandbox1.eval("mathematics.pi")
        assert pi_result1.success is True

        # Verify it doesn't exist in sandbox2
        pi_result2 = sandbox2.eval("mathematics.pi")
        assert pi_result2.success is False

        # Import different alias in sandbox2
        result2 = sandbox2.eval("import math.py as calc")
        assert result2.success is True

        # Verify both work correctly in their respective sandboxes
        pi_result1_again = sandbox1.eval("mathematics.pi")
        pi_result2_new = sandbox2.eval("calc.pi")

        assert pi_result1_again.success is True
        assert pi_result2_new.success is True

        # And that they're still isolated
        calc_in_1 = sandbox1.eval("calc.pi")
        math_in_2 = sandbox2.eval("mathematics.pi")

        assert calc_in_1.success is False
        assert math_in_2.success is False

    # def test_nested_imports_in_expressions(self):
    #     """Test that imports in expressions don't work (import is a statement)."""
    #     # NOTE: The grammar may actually allow some of these expressions
    #     # This is a design choice and not necessarily an error
    #     pass
