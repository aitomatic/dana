"""
Test text functions in Dana core library.
"""

import pytest

from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
from dana.libs.corelib.register_corelib_functions import register_corelib_functions


class TestTextFunctions:
    """Test text functions registration and functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.registry = FunctionRegistry()
        register_corelib_functions(self.registry)

    def test_text_functions_registered(self):
        """Test that text functions are properly registered."""
        # Check that all text functions are registered in the local namespace
        assert "capitalize_words" in self.registry._functions["local"]
        assert "title_case" in self.registry._functions["local"]

    def test_capitalize_words_function(self):
        """Test capitalize_words function."""
        func = self.registry._functions["local"]["capitalize_words"][0]

        # Test basic functionality
        result = func.execute(None, "hello world")
        assert result == "Hello World"

        result = func.execute(None, "dana programming language")
        assert result == "Dana Programming Language"

        result = func.execute(None, "single")
        assert result == "Single"

    def test_title_case_function(self):
        """Test title_case function."""
        func = self.registry._functions["local"]["title_case"][0]

        # Test basic functionality
        result = func.execute(None, "hello world")
        assert result == "Hello World"

        result = func.execute(None, "dana programming language")
        assert result == "Dana Programming Language"

        result = func.execute(None, "single")
        assert result == "Single"

    def test_function_argument_validation(self):
        """Test that functions properly validate their arguments."""
        capitalize_func = self.registry._functions["local"]["capitalize_words"][0]
        title_case_func = self.registry._functions["local"]["title_case"][0]

        # Test wrong argument types
        with pytest.raises(TypeError, match="capitalize_words argument must be a string"):
            capitalize_func.execute(None, 123)

        with pytest.raises(TypeError, match="title_case argument must be a string"):
            title_case_func.execute(None, 456)
