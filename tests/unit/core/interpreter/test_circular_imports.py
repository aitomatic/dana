#!/usr/bin/env python3
"""
Tests for circular import detection in Dana.

This module tests scenarios where modules import each other directly or indirectly,
which should be detected and handled gracefully.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from pathlib import Path

from dana.core.lang.dana_sandbox import DanaSandbox


class TestCircularImports:
    """Test class for circular import detection."""

    def setup_method(self):
        """Set up test fixtures with circular import test modules."""
        self.sandbox = DanaSandbox()

        # Set up test modules path
        test_modules_path = Path(__file__).parent / "test_modules_circular"
        self.test_modules_path = str(test_modules_path.resolve())

        # Create test module structure
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
        """Create test modules with circular dependencies."""
        base_path = Path(__file__).parent / "test_modules_circular"
        base_path.mkdir(exist_ok=True)

        # Direct circular imports: A imports B, B imports A
        (base_path / "circular_a.na").write_text("""
# Module A that imports B
import circular_b

I_AM = "circular_a"

def function_a():
    return "A calls " + circular_b.function_b()
""")

        (base_path / "circular_b.na").write_text("""
# Module B that imports A  
import circular_a

I_AM = "circular_b"

def function_b():
    return "B calls " + circular_a.I_AM
""")

        # Indirect circular imports: A -> B -> C -> A
        (base_path / "indirect_a.na").write_text("""
# Module A in indirect cycle
import indirect_b

I_AM = "indirect_a"
""")

        (base_path / "indirect_b.na").write_text("""
# Module B in indirect cycle
import indirect_c

I_AM = "indirect_b"
""")

        (base_path / "indirect_c.na").write_text("""
# Module C in indirect cycle
import indirect_a

I_AM = "indirect_c"
""")

    def test_direct_circular_import_detection(self):
        """Test detection of direct circular imports (A imports B, B imports A)."""
        # This should fail with circular import error
        result = self.sandbox.execute_string("import circular_a")

        assert result.success is False
        # Should get circular import error, not recursion depth error
        error_msg = str(result.error).lower()
        assert any(phrase in error_msg for phrase in ["circular", "cycle", "circular import"])

    def test_indirect_circular_import_detection(self):
        """Test detection of indirect circular imports (A -> B -> C -> A)."""
        # This should fail with circular import error
        result = self.sandbox.execute_string("import indirect_a")

        assert result.success is False
        # Should get circular import error, not recursion depth error
        error_msg = str(result.error).lower()
        assert any(phrase in error_msg for phrase in ["circular", "cycle", "circular import"])

    def test_non_circular_imports_work(self):
        """Test that non-circular imports still work correctly."""
        # Create a simple non-circular module
        base_path = Path(__file__).parent / "test_modules_circular"
        (base_path / "simple.na").write_text("""
# Simple non-circular module
I_AM = "simple"

def simple_function():
    return "Simple works"
""")

        result = self.sandbox.execute_string("import simple")
        assert result.success is True

        func_result = self.sandbox.execute_string("simple.simple_function()")
        assert func_result.success is True
        assert "Simple works" in str(func_result.result)

    def test_circular_import_error_message_quality(self):
        """Test that circular import errors provide helpful messages."""
        result = self.sandbox.execute_string("import circular_a")

        assert result.success is False
        error_msg = str(result.error)

        # Should mention the modules involved in the cycle
        assert "circular_a" in error_msg or "circular_b" in error_msg
        # Should be a clear error type
        assert any(phrase in error_msg.lower() for phrase in ["circular", "cycle"])

    def teardown_method(self):
        """Clean up test modules and environment."""
        import shutil

        test_modules_path = Path(__file__).parent / "test_modules_circular"
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
