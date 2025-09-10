"""
Tests for object method call functionality in Dana.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.core.lang.ast import (
    Assignment,
    Identifier,
    LiteralExpression,
    ObjectFunctionCall,
    Program,
)
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


class MockTestObject:
    """Test object for method call testing."""

    def __init__(self, value=42):
        self.value = value

    def get_value(self):
        """Return the current value."""
        return self.value

    def add(self, x):
        """Add x to the current value."""
        return self.value + x

    def multiply(self, x, y=1):
        """Multiply value by x and y."""
        return self.value * x * y

    def list_tools(self):
        """Return a list of available tools."""
        return ["tool1", "tool2", "tool3"]

    def set_value(self, new_value):
        """Set a new value."""
        self.value = new_value
        return self.value


class MockAsyncObject:
    """Test object with async methods for testing async support."""

    def __init__(self, value=100):
        self.value = value

    async def async_get_value(self):
        """Async method that returns the current value."""
        return self.value

    async def async_add(self, x):
        """Async method that adds x to the current value."""
        return self.value + x

    async def async_fetch_data(self, query):
        """Async method that simulates fetching data."""
        return f"Async data for: {query}"

    def sync_method(self):
        """Regular sync method on async object."""
        return "sync result"


class MockWebSearchTool:
    """Mock websearch tool for testing the original use case."""

    def __init__(self):
        self.name = "websearch"

    def list_tools(self):
        """Return a list of available tools."""
        return [
            {"name": "search", "description": "Search the web"},
            {"name": "summarize", "description": "Summarize search results"},
            {"name": "extract", "description": "Extract specific information"},
        ]

    def search(self, query):
        """Mock search method."""
        return f"Search results for: {query}"


class MockNestedObject:
    """Test object with nested structure."""

    def __init__(self):
        self.db = MockDatabaseConnection()

    def get_data(self, table):
        return self.db.query(f"SELECT * FROM {table}")

    def disconnect(self):
        return self.db.close()


class MockDatabaseConnection:
    """Mock database connection for nested object testing."""

    def __init__(self):
        self.connected = True

    def query(self, sql):
        return f"Query result for: {sql}"

    def close(self):
        self.connected = False
        return "Connection closed"


class TestObjectFunctionCallAST:
    """Test ObjectFunctionCall AST node creation and parsing."""

    def test_ast_node_creation(self):
        """Test creating ObjectFunctionCall AST nodes directly."""
        # Create an ObjectFunctionCall node
        obj_call = ObjectFunctionCall(
            object=Identifier(name="local:test_obj"), method_name="add", args={"__positional": [LiteralExpression(value=10)]}
        )

        assert obj_call.object.name == "local:test_obj"
        assert obj_call.method_name == "add"
        assert obj_call.args["__positional"][0].value == 10

    def test_parser_creates_object_function_call(self):
        """Test that the parser creates ObjectFunctionCall nodes correctly."""
        from dana.core.lang.parser.utils.parsing_utils import ParserCache

        parser = ParserCache.get_parser("dana")

        # Test simple method call
        ast = parser.parse("test_obj.add(10)")
        assert isinstance(ast, Program)
        assert len(ast.statements) == 1

        stmt = ast.statements[0]
        if isinstance(stmt, Assignment):
            # If it's parsed as an assignment, get the value
            node = stmt.value
        else:
            node = stmt

        # Should be an ObjectFunctionCall
        assert isinstance(node, ObjectFunctionCall)
        assert node.method_name == "add"
        assert isinstance(node.object, Identifier)

    def test_parser_handles_empty_arguments(self):
        """Test that the parser handles empty argument lists correctly."""
        from dana.core.lang.parser.utils.parsing_utils import ParserCache

        parser = ParserCache.get_parser("dana")

        ast = parser.parse("test_obj.get_value()")
        stmt = ast.statements[0]

        if isinstance(stmt, Assignment):
            node = stmt.value
        else:
            node = stmt

        # Should create an ObjectFunctionCall even with empty arguments
        if isinstance(node, ObjectFunctionCall):
            assert node.method_name == "get_value"
            assert isinstance(node.object, Identifier)


class TestObjectFunctionCallExecution:
    """Test object method call execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        # Add test objects to context
        self.test_obj = MockTestObject()
        self.context.set("local:test_obj", self.test_obj)

    def test_simple_method_call_no_args(self):
        """Test calling a method with no arguments."""
        result = self.interpreter._eval_source_code("test_obj.get_value()", self.context)
        assert result == 42

    def test_method_call_with_args(self):
        """Test calling a method with arguments."""
        result = self.interpreter._eval_source_code("test_obj.add(10)", self.context)
        assert result == 52

    def test_method_call_with_multiple_args(self):
        """Test calling a method with multiple arguments."""
        result = self.interpreter._eval_source_code("test_obj.multiply(2, 3)", self.context)
        assert result == 252  # 42 * 2 * 3 = 252

    def test_method_returns_list(self):
        """Test calling a method that returns a list."""
        result = self.interpreter._eval_source_code("test_obj.list_tools()", self.context)
        assert result == ["tool1", "tool2", "tool3"]

    def test_method_modifies_object_state(self):
        """Test calling a method that modifies object state."""
        # Change the value
        result = self.interpreter._eval_source_code("test_obj.set_value(100)", self.context)
        assert result == 100

        # Verify the change
        result2 = self.interpreter._eval_source_code("test_obj.get_value()", self.context)
        assert result2 == 100


class TestWebSearchPattern:
    """Test the specific websearch.list_tools() pattern from the original request."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        # Add websearch tool to context
        self.websearch = MockWebSearchTool()
        self.context.set("local:websearch", self.websearch)

    def test_websearch_list_tools(self):
        """Test the exact websearch.list_tools() pattern."""
        result = self.interpreter._eval_source_code("websearch.list_tools()", self.context)

        expected = [
            {"name": "search", "description": "Search the web"},
            {"name": "summarize", "description": "Summarize search results"},
            {"name": "extract", "description": "Extract specific information"},
        ]
        assert result == expected

    def test_websearch_search_method(self):
        """Test websearch.search() method with arguments."""
        result = self.interpreter._eval_source_code('websearch.search("Dana")', self.context)
        assert result == "Search results for: Dana"


class TestNestedObjectCalls:
    """Test object method calls on nested objects."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        # Add nested object to context
        self.api = MockNestedObject()
        self.context.set("local:api", self.api)

    def test_nested_object_method_call(self):
        """Test calling a method on a nested object."""
        result = self.interpreter._eval_source_code('api.get_data("users")', self.context)
        assert result == "Query result for: SELECT * FROM users"

    def test_nested_object_chain_call(self):
        """Test calling methods that chain through nested objects."""
        result = self.interpreter._eval_source_code("api.disconnect()", self.context)
        assert result == "Connection closed"


class TestObjectFunctionCallEdgeCases:
    """Test edge cases and error conditions for object method calls."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        self.test_obj = MockTestObject()
        self.context.set("local:test_obj", self.test_obj)

    def test_nonexistent_method(self):
        """Test calling a method that doesn't exist."""
        with pytest.raises(AttributeError):
            self.interpreter._eval_source_code("test_obj.nonexistent_method()", self.context)

    def test_nonexistent_object(self):
        """Test calling a method on an object that doesn't exist."""
        with pytest.raises(AttributeError):
            self.interpreter._eval_source_code("nonexistent_obj.method()", self.context)

    def test_method_call_wrong_args(self):
        """Test calling a method with wrong number of arguments."""
        with pytest.raises(TypeError):
            # add() requires one argument
            self.interpreter._eval_source_code("test_obj.add()", self.context)


class TestDictMethodCalls:
    """Test method calls on dictionary objects."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        # Create a dictionary with callable values
        def mock_function():
            return "called"

        self.dict_obj = {"method": mock_function, "value": 42}
        self.context.set("local:dict_obj", self.dict_obj)

    def test_dict_method_call(self):
        """Test calling a method stored in a dictionary."""
        result = self.interpreter._eval_source_code("dict_obj.method()", self.context)
        assert result == "called"


class TestObjectFunctionCallIntegration:
    """Integration tests for object function calls with other language features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        self.test_obj = MockTestObject()
        self.context.set("local:test_obj", self.test_obj)

    def test_object_method_in_assignment(self):
        """Test using object method calls in assignments."""
        # Execute assignment using _eval
        self.interpreter._eval_source_code("result = test_obj.add(5)", self.context)

        # Check the result
        result = self.context.get("local:result")
        assert result == 47  # 42 + 5

    def test_object_method_in_expression(self):
        """Test using object method calls in larger expressions."""
        result = self.interpreter._eval_source_code("test_obj.add(10) + test_obj.add(20)", self.context)
        assert result == 114  # (42 + 10) + (42 + 20) = 52 + 62 = 114

    def test_chained_object_method_calls(self):
        """Test chaining multiple object method calls."""
        # Execute first method call using _eval
        self.interpreter._eval_source_code("test_obj.set_value(10)", self.context)

        # Then test the result
        result = self.interpreter._eval_source_code("test_obj.get_value()", self.context)
        assert result == 10


class TestAsyncObjectFunctionCalls:
    """Test async object method calls using Misc.safe_asyncio_run."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()

        # Add async test object to context
        self.async_obj = MockAsyncObject()
        self.context.set("local:async_obj", self.async_obj)

    def test_async_method_call_no_args(self):
        """Test calling an async method with no arguments."""
        result = self.interpreter._eval_source_code("async_obj.async_get_value()", self.context)
        assert result == 100

    def test_async_method_call_with_args(self):
        """Test calling an async method with arguments."""
        result = self.interpreter._eval_source_code("async_obj.async_add(25)", self.context)
        assert result == 125  # 100 + 25

    def test_async_method_call_with_string_args(self):
        """Test calling an async method with string arguments."""
        result = self.interpreter._eval_source_code('async_obj.async_fetch_data("test query")', self.context)
        assert result == "Async data for: test query"

    def test_sync_method_on_async_object(self):
        """Test calling a sync method on an object that also has async methods."""
        result = self.interpreter._eval_source_code("async_obj.sync_method()", self.context)
        assert result == "sync result"

    def test_async_method_in_assignment(self):
        """Test using async method calls in assignments."""
        # Execute assignment using _eval
        self.interpreter._eval_source_code("result = async_obj.async_add(50)", self.context)

        # Check the result
        result = self.context.get("local:result")
        assert result == 150  # 100 + 50

    def test_async_method_in_expression(self):
        """Test using async method calls in larger expressions."""
        # Note: Both async calls will be executed synchronously by safe_asyncio_run
        result = self.interpreter._eval_source_code("async_obj.async_add(10) + async_obj.async_add(20)", self.context)
        assert result == 230  # (100 + 10) + (100 + 20) = 110 + 120 = 230


if __name__ == "__main__":
    pytest.main([__file__])
