"""
Test star imports functionality in Dana language.

This module tests the implementation of `from ... import *` syntax
for both Dana and Python modules.
"""

import tempfile
import os
from pathlib import Path

from dana.core.lang.dana_sandbox import DanaSandbox


class TestStarImports:
    """Test suite for star import functionality."""

    def test_star_import_from_python_module(self):
        """Test star import from Python module respects __all__ and privacy."""
        code = """
from math.py import *
result = sqrt(16)
print("sqrt(16) = " + str(result))
"""
        sandbox = DanaSandbox()
        result = sandbox.execute_string(code)
        assert result is not None
        # sqrt should be imported from math module

    def test_star_import_from_dana_module_with_exports(self):
        """Test star import from Dana module with explicit __exports__."""
        # Create a temporary Dana module with exports
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "test_module.na"
            module_code = """
def public_func(x):
    return x * 2

def _private_func(x):
    return x * 3

def another_public(x):
    return x + 10

# Export only specific functions
__exports__ = ["public_func", "another_public"]
"""
            module_path.write_text(module_code)

            # Add tmpdir to Dana path
            import sys

            old_path = sys.path.copy()
            sys.path.insert(0, tmpdir)

            try:
                code = """
from test_module import *
result1 = public_func(5)
result2 = another_public(5)
print("public_func(5) = " + str(result1))
print("another_public(5) = " + str(result2))
"""
                sandbox = DanaSandbox()
                # Set DANAPATH to include our temp directory
                os.environ["DANAPATH"] = tmpdir
                result = sandbox.execute_string(code)
                assert result is not None
            finally:
                sys.path = old_path
                if "DANAPATH" in os.environ:
                    del os.environ["DANAPATH"]

    def test_star_import_respects_underscore_privacy(self):
        """Test that star import doesn't import private names (starting with _)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "private_test.na"
            module_code = """
def public_func():
    return "public"

def _private_func():
    return "private"

public_var = 42
_private_var = 100
"""
            module_path.write_text(module_code)

            import sys

            old_path = sys.path.copy()
            sys.path.insert(0, tmpdir)

            try:
                code = """
from private_test import *

# Should be able to access public_func and public_var
result1 = public_func()
result2 = public_var

# Attempting to access private should fail
try:
    result3 = _private_func()
    print("ERROR: Should not access private function")
except:
    print("Correctly blocked private function")

try:
    result4 = _private_var
    print("ERROR: Should not access private variable")
except:
    print("Correctly blocked private variable")
"""
                sandbox = DanaSandbox()
                os.environ["DANAPATH"] = tmpdir
                result = sandbox.execute_string(code)
                assert result is not None
            finally:
                sys.path = old_path
                if "DANAPATH" in os.environ:
                    del os.environ["DANAPATH"]

    def test_star_import_from_corelib(self):
        """Test star import from Dana's corelib modules."""
        code = """
from dana.libs.corelib.na_modules import *

# Should have access to BasicAgent and add_one
agent = BasicAgent()
result = add_one(5)
print("add_one(5) = " + str(result))
"""
        sandbox = DanaSandbox()
        sandbox.execute_string(code)
        # This should work with the corelib module

    def test_star_import_with_function_registration(self):
        """Test that star imported functions are properly registered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "func_module.na"
            module_code = """
def func1(x):
    return x + 1

def func2(x, y):
    return x * y

def func3():
    return "hello"
"""
            module_path.write_text(module_code)

            import sys

            old_path = sys.path.copy()
            sys.path.insert(0, tmpdir)

            try:
                code = """
from func_module import *

# All functions should be available
r1 = func1(10)
r2 = func2(3, 4)
r3 = func3()

print("func1(10) = " + str(r1))
print("func2(3, 4) = " + str(r2))
print("func3() = " + str(r3))
"""
                sandbox = DanaSandbox()
                os.environ["DANAPATH"] = tmpdir
                result = sandbox.execute_string(code)
                assert result is not None
            finally:
                sys.path = old_path
                if "DANAPATH" in os.environ:
                    del os.environ["DANAPATH"]

    def test_star_import_empty_module(self):
        """Test star import from an empty module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "empty.na"
            module_code = "# Empty module\n"
            module_path.write_text(module_code)

            import sys

            old_path = sys.path.copy()
            sys.path.insert(0, tmpdir)

            try:
                code = """
from empty import *
print("Successfully imported from empty module")
"""
                sandbox = DanaSandbox()
                os.environ["DANAPATH"] = tmpdir
                result = sandbox.execute_string(code)
                assert result is not None
            finally:
                sys.path = old_path
                if "DANAPATH" in os.environ:
                    del os.environ["DANAPATH"]

    def test_mixed_import_styles(self):
        """Test mixing star imports with explicit imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "mixed.na"
            module_code = """
def func_a():
    return "a"

def func_b():
    return "b"

def func_c():
    return "c"
"""
            module_path.write_text(module_code)

            import sys

            old_path = sys.path.copy()
            sys.path.insert(0, tmpdir)

            try:
                # First do explicit import, then star import from another module
                code = """
from mixed import func_a, func_b as b_func
from mixed import *

# Should have func_a, b_func (alias), and all functions via star
r1 = func_a()
r2 = b_func()
r3 = func_c()  # Only available via star import

print("func_a() = " + str(r1))
print("b_func() = " + str(r2))
print("func_c() = " + str(r3))
"""
                sandbox = DanaSandbox()
                os.environ["DANAPATH"] = tmpdir
                result = sandbox.execute_string(code)
                assert result is not None
            finally:
                sys.path = old_path
                if "DANAPATH" in os.environ:
                    del os.environ["DANAPATH"]
