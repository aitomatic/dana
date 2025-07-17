"""
Comprehensive test suite for PipelineExpression functionality.

This module provides comprehensive testing for the new PipelineExpression feature
including implicit first-argument mode, explicit placeholder mode, and edge cases.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
import pytest
from pathlib import Path
from typing import Any

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


def get_na_files():
    """Get all .na test files in the current directory."""
    test_dir = Path(__file__).parent
    return list(test_dir.glob("test_*.na"))


class TestPipelineComprehensive:
    """Comprehensive test suite for PipelineExpression."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

    def run_dana_test_file(self, file_path: str) -> Any:
        """Run a .na test file and return the result."""
        file_path = Path(file_path)
        if not file_path.exists():
            pytest.skip(f"Test file {file_path} not found")
        
        with open(file_path, 'r') as f:
            code = f.read()
        
        return self.interpreter._eval(code, self.context)

    @pytest.mark.parametrize("na_file", get_na_files())
    def test_pipeline_files(self, na_file: Path):
        """Auto-discover and run all .na test files in the directory."""
        result = self.run_dana_test_file(str(na_file))
        assert result is None  # Test functions handle their own assertions

    def test_basic_pipeline_expressions(self):
        """Test basic pipeline expressions with various data types."""
        code = '''
def double_value(x: int) -> int:
    return x * 2

def add_value(x: int, y: int) -> int:
    return x + y

# Basic pipeline
result = 5 | double_value | add_value(10)
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == 20  # 5 * 2 + 10

    def test_string_pipeline_operations(self):
        """Test string operations in pipelines."""
        code = '''
def capitalize_words(text: str) -> str:
    return text.title()

def add_surrounding(text: str, surround: str) -> str:
    return f"{surround}{text}{surround}"

result = "hello world" | capitalize_words | add_surrounding("***")
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == "***Hello World***"

    def test_list_pipeline_operations(self):
        """Test list operations in pipelines."""
        code = '''
def add_item(lst: list, item: Any) -> list:
    return lst + [item]

def double_list(lst: list) -> list:
    return lst * 2

result = [1, 2] | add_item(3) | double_list
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == [1, 2, 3, 1, 2, 3]

    def test_placeholder_substitution(self):
        """Test explicit placeholder substitution."""
        code = '''
def format_message(prefix: str, text: str, suffix: str) -> str:
    return f"{prefix}{text}{suffix}"

def wrap_text(text: str, wrapper: str) -> str:
    return f"{wrapper}{text}{wrapper}"

result = "test" | format_message("(", $, ")") | wrap_text("*")
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == "*(test)*"

    def test_complex_pipeline(self):
        """Test complex multi-stage pipeline."""
        code = '''
def process_data(data: str) -> str:
    return data.upper()

def add_metadata(data: str, metadata: str) -> str:
    return f"{metadata}: {data}"

def format_output(data: str, format_type: str) -> str:
    return f"[{format_type}] {data}"

result = "hello" | process_data | add_metadata("processed") | format_output("json")
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == "[json] processed: HELLO"

    def test_error_handling(self):
        """Test error handling in pipelines."""
        code = '''
def failing_function(x: Any) -> Any:
    raise ValueError("Test error")

try:
    result = "test" | failing_function
except ValueError as e:
    result = str(e)
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert "Test error" in str(result)

    def test_edge_cases(self):
        """Test edge cases in pipeline operations."""
        # Test empty pipeline (should return callable that returns input)
        code = '''
def identity(x: Any) -> Any:
    return x

result = 42 | identity
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == 42

        # Test single stage
        code = '''
def simple_func(x: int) -> int:
    return x + 1

result = 5 | simple_func
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == 6

    def test_type_coercion_in_pipelines(self):
        """Test type coercion in pipeline operations."""
        code = '''
def string_length(s: str) -> int:
    return len(s)

def multiply_by_factor(n: int, factor: int) -> int:
    return n * factor

result = "hello" | string_length | multiply_by_factor(3)
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == 15  # len("hello") * 3

    def test_placeholder_edge_cases(self):
        """Test edge cases with placeholder usage."""
        code = '''
def format_with_placeholders(a: str, b: str, c: str) -> str:
    return f"{a}|{b}|{c}"

def double_string(s: str) -> str:
    return s * 2

# Multiple placeholders in same call
result = "middle" | format_with_placeholders("start", $, "end") | double_string
'''
        result = self.interpreter._eval(code, SandboxContext())
        assert result == "start|middle|endstart|middle|end"


def test_pipeline_integration():
    """Integration test for pipeline functionality."""
    interpreter = DanaInterpreter()
    
    # Test actual Dana language code
    test_code = '''
def add_prefix(text: str, prefix: str = "Result: ") -> str:
    return f"{prefix}{text}"

def to_upper(text: str) -> str:
    return text.upper()

final_result = "pipeline test" | add_prefix("Processed: ") | to_upper
'''
    
    context = SandboxContext()
    result = interpreter._eval(test_code, context)
    assert result == "PROCESSED: PIPELINE TEST"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])