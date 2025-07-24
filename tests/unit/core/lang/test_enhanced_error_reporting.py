"""
Unit tests for enhanced error reporting in Dana.

Tests that errors include:
- File names
- Line numbers 
- Column numbers
- Source code context
- Stack traces
"""

import pytest
from pathlib import Path
import tempfile

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.common.exceptions import EnhancedDanaError


class TestEnhancedErrorReporting:
    """Test enhanced error reporting functionality."""
    
    def test_attribute_error_shows_location(self):
        """Test that AttributeError shows file, line, column and source."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as f:
            f.write("""# Test file
x = None
y = x.missing_attr  # Error on line 3
""")
            f.flush()
            
            try:
                result = DanaSandbox.quick_run(f.name)
                assert result.success is False
                error = result.error
                
                # Check error type
                assert isinstance(error, EnhancedDanaError)
                
                # Check error message contains location info
                error_str = str(error)
                assert "line 3" in error_str
                assert "column" in error_str
                assert "missing_attr" in error_str
                assert "'NoneType' object has no attribute" in error_str
                
                # Check error has location attributes
                assert error.line == 3
                assert error.column is not None
                assert error.filename == f.name
                
            finally:
                Path(f.name).unlink()
    
    def test_nested_function_error_shows_stack(self):
        """Test that errors in nested functions show call stack."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as f:
            f.write("""# Test nested functions
def inner_func(x):
    return x.bad_attr  # Error here

def outer_func(y):
    return inner_func(y)

result = outer_func(None)
""")
            f.flush()
            
            try:
                result = DanaSandbox.quick_run(f.name)
                assert result.success is False
                error = result.error
                
                # Check error contains function names in message
                error_str = str(error)
                assert "inner_func" in error_str or "line 3" in error_str
                assert "bad_attr" in error_str
                
            finally:
                Path(f.name).unlink()
    
    def test_syntax_error_shows_location(self):
        """Test that syntax errors show location."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as f:
            f.write("""# Test syntax error
x = 1 +   # Incomplete expression
""")
            f.flush()
            
            try:
                result = DanaSandbox.quick_run(f.name)
                assert result.success is False
                
                # Syntax errors should at least show the file
                error_str = str(result.error)
                assert "line 2" in error_str.lower() or "syntax" in error_str.lower()
                
            finally:
                Path(f.name).unlink()
    
    def test_error_in_expression(self):
        """Test error reporting in complex expressions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as f:
            f.write("""# Test expression error
data = {"key": None}
result = data["key"].some_method()  # Error on accessing None.some_method
""")
            f.flush()
            
            try:
                result = DanaSandbox.quick_run(f.name)
                assert result.success is False
                
                error_str = str(result.error)
                assert "some_method" in error_str
                assert "NoneType" in error_str
                
            finally:
                Path(f.name).unlink()
    
    def test_multiple_errors_in_file(self):
        """Test that first error is reported with correct location."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.na', delete=False) as f:
            f.write("""# Multiple potential errors
x = None
y = x.first_error  # First error here
z = y.second_error  # This won't execute
""")
            f.flush()
            
            try:
                result = DanaSandbox.quick_run(f.name)
                assert result.success is False
                
                error_str = str(result.error)
                assert "first_error" in error_str
                assert "line 3" in error_str
                # Should not reach second error
                assert "second_error" not in error_str
                
            finally:
                Path(f.name).unlink()
    
    def test_error_in_imported_module(self):
        """Test error reporting across module boundaries."""
        # This test is a placeholder for future module import support
        pass
    
    def test_repl_mode_error_formatting(self):
        """Test that REPL mode errors are formatted appropriately."""
        sandbox = DanaSandbox()
        
        # Test simple REPL error - use newline instead of semicolon
        result = sandbox.eval("x = None\ny = x.missing")
        assert result.success is False
        
        # REPL errors should be concise but still informative
        error_str = str(result.error)
        assert "missing" in error_str
        assert "NoneType" in error_str