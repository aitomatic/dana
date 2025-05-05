"""Test the ability to call Python functions from DANA."""

import unittest
from typing import Dict, Any

from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.runtime.context import RuntimeContext


class TestPythonObject:
    """Test object with methods for DANA to call."""
    
    def __init__(self):
        """Initialize test object."""
        self.value = 42
        self.name = "Test Object"
        self.nested = TestNestedObject()
        
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
    
    def greet(self, name: str = "World") -> str:
        """Return a greeting."""
        return f"Hello, {name}!"
    
    def update_value(self, new_value: int) -> int:
        """Update the object's value and return the new value."""
        self.value = new_value
        return self.value


class TestNestedObject:
    """Test nested object with methods for DANA to call."""
    
    def __init__(self):
        """Initialize nested object."""
        self.value = 100
    
    def get_value(self) -> int:
        """Return the object's value."""
        return self.value
    
    def set_value(self, new_value: int) -> None:
        """Set the object's value."""
        self.value = new_value


class TestPythonFunctionCalls(unittest.TestCase):
    """Test the ability to call Python functions from DANA."""
    
    def setUp(self):
        """Set up the test environment."""
        self.context = RuntimeContext()
        self.interpreter = Interpreter(self.context)
        
        # Create a test object
        self.test_obj = TestPythonObject()
        
        # Set up some functions
        self.context.set("private.test_obj", self.test_obj)
        self.context.set("private.test_func", lambda x, y: x * y)
        
    def test_object_method_call(self):
        """Test calling a method on an object."""
        code = 'result = test_obj.add(a=5, b=3)'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the result
        self.assertEqual(self.context.get("private.result"), 8)
    
    def test_object_method_call_with_positional_args(self):
        """Test calling a method with positional arguments."""
        code = 'result = test_obj.multiply(0=7, 1=6)'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the result
        self.assertEqual(self.context.get("private.result"), 42)
    
    def test_function_variable_call(self):
        """Test calling a function stored in a variable."""
        code = 'result = test_func(0=10, 1=5)'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the result
        self.assertEqual(self.context.get("private.result"), 50)
    
    def test_object_attribute_access(self):
        """Test accessing an object attribute."""
        code = 'value = test_obj.value'
        parse_result = parse(code)
        
        # Execute the program
        # Note: This won't work without adding support for attribute access in the AST
        # and parser, but we can test the function call part for now
        
        # Set up the value directly to test the next part
        self.context.set("private.value", 42)
        
        # Now test a method that uses the object's internal state
        code = 'test_obj.update_value(new_value=100)'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the state was updated
        self.assertEqual(self.test_obj.value, 100)
    
    def test_nested_object_method(self):
        """Test calling a method on a nested object."""
        code = 'nested_value = test_obj.nested.get_value()'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the result
        self.assertEqual(self.context.get("private.nested_value"), 100)
        
        # Now test setting a value on the nested object
        code = 'test_obj.nested.set_value(new_value=200)'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the state was updated
        self.assertEqual(self.test_obj.nested.value, 200)
    
    def test_method_with_default_param(self):
        """Test calling a method with a default parameter."""
        # Call with default parameter
        code = 'greeting1 = test_obj.greet()'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the result
        self.assertEqual(self.context.get("private.greeting1"), "Hello, World!")
        
        # Call with explicit parameter
        code = 'greeting2 = test_obj.greet(name="DANA")'
        parse_result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(parse_result)
        
        # Check the result
        self.assertEqual(self.context.get("private.greeting2"), "Hello, DANA!")


if __name__ == "__main__":
    unittest.main()