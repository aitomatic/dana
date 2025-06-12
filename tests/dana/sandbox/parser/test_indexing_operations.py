"""
Test suite for square bracket indexing operations.

Tests the fix for indexing operations where expressions like obj[key] 
were incorrectly returning the base object instead of the indexed value.
"""

import pytest

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestIndexingOperations:
    """Test suite for square bracket indexing operations."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.parser = DanaParser()
        self.context = SandboxContext()
        self.interpreter = DanaInterpreter()

    def test_dictionary_indexing(self):
        """Test basic dictionary indexing operations."""
        dana_code = '''
test_dict = {"key": "value", "num": 42}
result1 = test_dict["key"]
result2 = test_dict["num"]
'''
        
        # Parse and execute
        ast = self.parser.parse(dana_code)
        self.interpreter.execute_program(ast, self.context)
        
        # Verify results
        result1 = self.context.get("result1")
        result2 = self.context.get("result2")
        
        assert result1 == "value", f"Expected 'value', got {result1}"
        assert result2 == 42, f"Expected 42, got {result2}"
        
        # Ensure we're not getting the whole dictionary back
        test_dict = self.context.get("test_dict")
        assert result1 != test_dict, "Should not return entire dictionary"
        assert result2 != test_dict, "Should not return entire dictionary"

    def test_list_indexing(self):
        """Test basic list indexing operations."""
        dana_code = '''
test_list = [1, 2, 3, 4]
result1 = test_list[0]
result2 = test_list[-1]
result3 = test_list[2]
'''
        
        # Parse and execute
        ast = self.parser.parse(dana_code)
        self.interpreter.execute_program(ast, self.context)
        
        # Verify results
        result1 = self.context.get("result1")
        result2 = self.context.get("result2")
        result3 = self.context.get("result3")
        
        assert result1 == 1, f"Expected 1, got {result1}"
        assert result2 == 4, f"Expected 4, got {result2}"
        assert result3 == 3, f"Expected 3, got {result3}"
        
        # Ensure we're not getting the whole list back
        test_list = self.context.get("test_list")
        assert result1 != test_list, "Should not return entire list"

    def test_pandas_indexing(self):
        """Test pandas DataFrame iloc indexing operations."""
        dana_code = '''
import pandas.py as pd
df = pd.DataFrame({"col": [10, 20, 30]})
result = df.iloc[0]
'''
        
        # Parse and execute
        ast = self.parser.parse(dana_code)
        self.interpreter.execute_program(ast, self.context)
        
        # Verify results
        result = self.context.get("result")
        
        # Check that result is not the indexer object itself
        import pandas as pd
        assert not isinstance(result, pd.core.indexing._iLocIndexer), \
            f"Should not return indexer object, got {type(result)}"
        
        # Check that result is a pandas Series (the expected return type)
        assert isinstance(result, pd.Series), \
            f"Expected pandas Series, got {type(result)}"
        
        # Check the actual value
        assert result.iloc[0] == 10, f"Expected first value to be 10, got {result.iloc[0]}"

    def test_nested_indexing(self):
        """Test nested indexing operations."""
        dana_code = '''
nested_dict = {"data": {"inner": [1, 2, 3]}}
result1 = nested_dict["data"]
result2 = nested_dict["data"]["inner"]
result3 = nested_dict["data"]["inner"][1]
'''
        
        # Parse and execute
        ast = self.parser.parse(dana_code)
        self.interpreter.execute_program(ast, self.context)
        
        # Verify results
        result1 = self.context.get("result1")
        result2 = self.context.get("result2")
        result3 = self.context.get("result3")
        
        assert result1 == {"inner": [1, 2, 3]}, f"Expected inner dict, got {result1}"
        assert result2 == [1, 2, 3], f"Expected list, got {result2}"
        assert result3 == 2, f"Expected 2, got {result3}"

    def test_indexing_error_handling(self):
        """Test that indexing operations properly raise errors for invalid keys/indices."""
        # Test KeyError for dictionary
        dana_code_dict = '''
test_dict = {"key": "value"}
result = test_dict["nonexistent"]
'''
        
        ast = self.parser.parse(dana_code_dict)
        with pytest.raises(Exception):  # Should raise some form of error
            self.interpreter.execute_program(ast, self.context)
        
        # Test IndexError for list
        dana_code_list = '''
test_list = [1, 2, 3]
result = test_list[10]
'''
        
        # Reset context for new test
        self.context = SandboxContext()
        self.interpreter = DanaInterpreter()
        
        ast = self.parser.parse(dana_code_list)
        with pytest.raises(Exception):  # Should raise some form of error
            self.interpreter.execute_program(ast, self.context) 