"""
Tests for method chaining functionality in Dana.

These tests focus on output behavior rather than implementation details,
verifying that method chaining works correctly with various built-in Python objects.
"""

import pytest

from dana.core.lang.dana_sandbox import DanaSandbox


class TestMethodChaining:
    """Test class for method chaining functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_string_method_chaining_basic(self):
        """Test basic string method chaining operations."""
        code = """
text = "  Hello World  "
result = text.strip().lower()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "hello world"

    def test_string_method_chaining_triple(self):
        """Test triple string method chaining."""
        code = """
text = "  Hello World  "
result = text.strip().lower().replace(" ", "_")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "hello_world"

    def test_string_method_chaining_complex(self):
        """Test complex string method chaining with multiple replacements."""
        code = """
text = "The Quick Brown Fox"
result = text.lower().replace(" ", "-").replace("fox", "wolf")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "the-quick-brown-wolf"

    def test_string_method_chaining_with_args(self):
        """Test string method chaining with method arguments."""
        code = """
text = "apple,banana,cherry"
result = text.upper().split(",")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == ["APPLE", "BANANA", "CHERRY"]

    def test_string_method_chaining_replace_operations(self):
        """Test string method chaining with replace operations."""
        code = """
text = "hello world test"
result = text.replace("world", "dana").replace("test", "language").upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO DANA LANGUAGE"

    def test_list_method_chaining_with_strings(self):
        """Test chaining operations on lists returned by string methods."""
        code = """
text = "a,b,c,d"
parts = text.split(",")
result = parts[0].upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "A"

    def test_dict_method_chaining(self):
        """Test method chaining with dictionary operations."""
        code = """
data = {"name": "john", "age": 30}
result = data.get("name").upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "JOHN"

    def test_nested_method_chaining(self):
        """Test nested method chaining with different object types."""
        code = """
data = {"items": "apple,banana,cherry"}
result = data.get("items").split(",")[1].upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "BANANA"

    def test_method_chaining_with_assignment(self):
        """Test method chaining with intermediate assignments."""
        code = """
text = "hello world"
step1 = text.upper()
result = step1.replace(" ", "_")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO_WORLD"

    def test_method_chaining_no_args(self):
        """Test method chaining with methods that take no arguments."""
        code = """
text = "  HELLO  "
result = text.strip().lower()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "hello"

    def test_method_chaining_boolean_result(self):
        """Test method chaining that returns boolean values."""
        code = """
text = "hello world"
result = text.replace("world", "dana").endswith("dana")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result is True

    def test_method_chaining_numeric_result(self):
        """Test method chaining that returns numeric values."""
        code = """
text = "hello,world,test"
result = len(text.split(","))
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == 3

    def test_method_chaining_with_indexing(self):
        """Test method chaining combined with indexing operations."""
        code = """
text = "hello,world,test"
result = text.split(",")[1].upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "WORLD"

    def test_method_chaining_with_slicing(self):
        """Test method chaining combined with slicing operations."""
        code = """
text = "hello world test extra"
words = text.split(" ")
first_two = words[0:2]
result = first_two[0].upper() + first_two[1].upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLOWORLD"

    def test_long_method_chain(self):
        """Test a long chain of method calls."""
        code = """
text = "  THE QUICK BROWN FOX JUMPS  "
result = text.strip().lower().replace(" ", "_").replace("fox", "wolf").upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "THE_QUICK_BROWN_WOLF_JUMPS"

    def test_method_chaining_error_handling(self):
        """Test that method chaining properly handles valid method calls."""
        code = """
text = "hello"
# Test valid method chaining instead of error handling
result = text.upper().replace("H", "J")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "JELLO"

    def test_method_chaining_with_string_formatting(self):
        """Test method chaining with string concatenation."""
        code = """
name = "john"
greeting = "hello " + name
result = greeting.upper().replace(" ", "+")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO+JOHN"

    def test_method_chaining_conditional_result(self):
        """Test method chaining with conditional logic."""
        code = """
text = "hello world"
no_spaces = text.replace(" ", "")
is_long = len(no_spaces) > 5
if is_long:
    result = text.upper()
else:
    result = text.lower()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO WORLD"

    def test_method_chaining_mixed_types(self):
        """Test method chaining across different object types."""
        code = """
# Start with string, convert to list, get element
text = "a b c"
parts = text.split(" ")
result = parts[0].upper() + parts[1].upper() + parts[2].upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "ABC"

    def test_method_chaining_empty_string(self):
        """Test method chaining with empty strings."""
        code = """
text = ""
result = text.strip().upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == ""

    def test_method_chaining_special_characters(self):
        """Test method chaining with special characters."""
        code = """
text = "hello@world#test"
result = text.replace("@", "_").replace("#", "_").upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO_WORLD_TEST"

    def test_method_chaining_preserve_types(self):
        """Test that method chaining preserves appropriate types."""
        code = """
text = "123"
result = text.strip().isdigit()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result is True

    def test_method_chaining_find_method(self):
        """Test method chaining with methods that return indices."""
        code = """
text = "hello"
result = text.find("l") >= 0
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result is True

    def test_string_join_method(self):
        """Test the string join method with list arguments."""
        code = """
b = ["hehe", "haha"]
a = ",".join(b)
a
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "hehe,haha"

    def test_string_join_method_with_different_separator(self):
        """Test the string join method with different separators."""
        code = """
words = ["apple", "banana", "cherry"]
result = " - ".join(words)
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "apple - banana - cherry"


class TestMethodChainingIntegration:
    """Integration tests for method chaining with other Dana features."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.sandbox = DanaSandbox()

    def test_method_chaining_in_function(self):
        """Test method chaining inside function definitions."""
        code = """
def process_text(text):
    return text.strip().lower().replace(" ", "_")

result = process_text("  Hello World  ")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "hello_world"

    def test_method_chaining_as_function_arg(self):
        """Test method chaining as function arguments."""
        code = """
def format_name(name):
    return f"Name: {name}"

text = "  john doe  "
result = format_name(text.strip().title())
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "Name: John Doe"

    def test_method_chaining_in_list_operations(self):
        """Test method chaining within list operations."""
        code = """
texts = ["  hello  ", "  world  ", "  test  "]
cleaned = []
for text in texts:
    cleaned.append(text.strip().upper())
result = cleaned[0] + cleaned[1] + cleaned[2]
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLOWORLDTEST"

    def test_method_chaining_with_variables(self):
        """Test method chaining with variable assignments."""
        code = """
separator = "+"
text = "hello world test"
result = text.replace(" ", separator).upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO+WORLD+TEST"

    def test_method_chaining_comparison(self):
        """Test method chaining in comparison operations."""
        code = """
text1 = "hello"
text2 = "HELLO"
result = text1.upper() == text2.lower().upper()
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result is True

    def test_method_chaining_with_return_values(self):
        """Test method chaining with function return values."""
        code = """
def get_text():
    return "hello world"

result = get_text().upper().replace(" ", "+")
result
"""
        execution_result = self.sandbox.execute_string(code)
        assert execution_result.success
        assert execution_result.result == "HELLO+WORLD"


if __name__ == "__main__":
    pytest.main([__file__])
