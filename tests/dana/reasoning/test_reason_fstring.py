"""Test reason() statements with f-strings."""

from typing import List, Union

from dana.sandbox.interpreter.interpreter import Interpreter

from opendxa.dana.sandbox.parser.ast import Expression, FStringExpression
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestFStringEvaluation:
    """Test f-string evaluation in the interpreter."""

    def test_fstring_evaluation(self):
        """Test that f-string expressions are properly evaluated."""
        # Create a context with some variables
        context = SandboxContext()
        interpreter = Interpreter(context)

        # Set up test variables
        context.set("private.a", 10)
        context.set("private.pi", 3.14)

        # Create a simple f-string expression that uses our special format
        parts: List[Union[Expression, str]] = ["F-STRING-PLACEHOLDER:What is {private.a}*{private.pi}?"]
        fstring = FStringExpression(parts=parts)

        # Process using the expression evaluator
        result = interpreter.expression_evaluator.evaluate_fstring_expression(fstring, {"private.a": 10, "private.pi": 3.14})

        # Check the result
        assert "What is 10*3.14?" in result, f"Expected '10*3.14' in result, got: {result}"
