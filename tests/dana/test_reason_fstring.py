"""Test reason() statements with f-strings."""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from opendxa.dana.language.ast import FStringExpression, Identifier
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel


class TestFStringEvaluation:
    """Test f-string evaluation in the interpreter."""
    
    def test_fstring_visit_node(self):
        """Test that f-string expressions are properly evaluated by visit_node."""
        # Create a context with some variables
        context = RuntimeContext()
        interpreter = Interpreter(context)
        
        # Set up test variables
        context.set("private.a", 10)
        context.set("private.pi", 3.14)
        
        # Create a simple f-string expression that uses our special format
        parts = ["F-STRING-PLACEHOLDER:What is {a}*{pi}?"]
        fstring = FStringExpression(parts=parts)
        
        # Process directly
        result = interpreter.visit_fstring_expression(fstring, {"a": 10, "pi": 3.14})
        
        # Check the result
        assert "What is 10*3.14?" in result, f"Expected '10*3.14' in result, got: {result}"