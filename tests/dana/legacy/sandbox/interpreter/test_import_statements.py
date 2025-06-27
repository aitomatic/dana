"""
Tests for import statement execution in Dana.

This module tests the execute_import_statement and execute_import_from_statement
methods in the StatementExecutor class.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter


class TestImportStatements:
    """Test class for import statement functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        from opendxa.dana.sandbox.parser.utils.parsing_utils import ParserCache

        self.parser = ParserCache.get_parser("dana")
        self.interpreter = DanaInterpreter()
        self.sandbox = DanaSandbox()

    def test_simple_import_python_module(self):
        """Test importing a Python module: import math.py."""
        result = self.sandbox.eval("import math.py")

        assert result.success is True
        assert result.result is None  # import statements return None

        # Test that the module is accessible
        pi_result = self.sandbox.eval("math.pi")
        assert pi_result.success is True
        assert abs(pi_result.result - 3.141592653589793) < 1e-10

    def test_import_with_alias(self):
        """Test importing with alias: import json.py as j."""
        result = self.sandbox.eval("import json.py as j")

        assert result.success is True
        assert result.result is None

        # Test that the aliased module is accessible
        dumps_result = self.sandbox.eval('j.dumps({"test": 123})')
        assert dumps_result.success is True
        assert dumps_result.result == '{"test": 123}'

    def test_from_import_basic(self):
        """Test from-import: from math.py import sqrt."""
        result = self.sandbox.eval("from math.py import sqrt")

        assert result.success is True
        assert result.result is None

        # Test that the imported function is accessible
        sqrt_result = self.sandbox.eval("sqrt(16)")
        assert sqrt_result.success is True
        assert sqrt_result.result == 4.0

    def test_from_import_with_alias(self):
        """Test from-import with alias: from json.py import dumps as json_dumps."""
        result = self.sandbox.eval("from json.py import dumps as json_dumps")

        assert result.success is True
        assert result.result is None

        # Test that the aliased function is accessible
        dumps_result = self.sandbox.eval('json_dumps({"hello": "world"})')
        assert dumps_result.success is True
        assert dumps_result.result == '{"hello": "world"}'

    def test_python_module_with_py_extension(self):
        """Test importing Python module with .py extension: import os.py."""
        result = self.sandbox.eval("import os.py as operating_system")

        assert result.success is True
        assert result.result is None

        # Test that the module is accessible
        getcwd_result = self.sandbox.eval("operating_system.getcwd()")
        assert getcwd_result.success is True
        assert isinstance(getcwd_result.result, str)

    def test_dana_module_not_found_error(self):
        """Test error handling for nonexistent Dana modules."""
        result = self.sandbox.eval("import nonexistent_module")

        assert result.success is False
        assert any(phrase in str(result.error).lower() for phrase in ["not found", "loading", "no module named"])

    def test_python_module_not_found_error(self):
        """Test error handling for nonexistent Python modules."""
        result = self.sandbox.eval("import nonexistent_module.py")

        assert result.success is False
        assert any(phrase in str(result.error).lower() for phrase in ["not found", "importing", "no module named"])

    def test_from_import_name_not_found_error(self):
        """Test error handling for nonexistent names in from-import."""
        result = self.sandbox.eval("from math.py import nonexistent_function")

        assert result.success is False
        assert "cannot import name" in str(result.error).lower()

    def test_multiple_imports_in_sequence(self):
        """Test multiple import statements in the same context."""
        # Import multiple modules
        result1 = self.sandbox.eval("import math.py")
        result2 = self.sandbox.eval("import json.py")
        result3 = self.sandbox.eval("from os.py import getcwd")

        assert result1.success is True
        assert result2.success is True
        assert result3.success is True

        # Test that all are accessible
        pi_result = self.sandbox.eval("math.pi")
        dumps_result = self.sandbox.eval('json.dumps({"test": 1})')
        getcwd_result = self.sandbox.eval("getcwd()")

        assert pi_result.success is True
        assert dumps_result.success is True
        assert getcwd_result.success is True

    def test_import_in_dana_context_isolation(self):
        """Test that imports are properly isolated between different contexts."""
        sandbox1 = DanaSandbox()
        sandbox2 = DanaSandbox()

        # Import in first sandbox only
        result1 = sandbox1.eval("import math.py")
        assert result1.success is True

        # Should be accessible in first sandbox
        pi_result1 = sandbox1.eval("math.pi")
        assert pi_result1.success is True

        # Should NOT be accessible in second sandbox
        pi_result2 = sandbox2.eval("math.pi")
        assert pi_result2.success is False

    @pytest.mark.parametrize(
        "module_name,expected_attr",
        [
            ("math.py", "pi"),
            ("json.py", "dumps"),
            ("os.py", "getcwd"),
            ("sys.py", "version"),
            ("datetime.py", "datetime"),
        ],
    )
    def test_various_python_modules(self, module_name, expected_attr):
        """Test importing various Python standard library modules."""
        result = self.sandbox.eval(f"import {module_name}")
        assert result.success is True

        # Get the module name without .py for accessing attributes
        module_name_clean = module_name[:-3]

        # Test accessing an attribute/function from the module
        attr_result = self.sandbox.eval(f"{module_name_clean}.{expected_attr}")
        assert attr_result.success is True
        assert attr_result.result is not None
