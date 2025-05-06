"""Test the reason statement functionality in DANA."""

import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from opendxa.dana.language.ast import (
    ReasonStatement,
    Identifier,
    LiteralExpression,
    Literal
)
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.common.types import BaseRequest, BaseResponse


class TestReasonStatement(unittest.TestCase):
    """Test the reason statement functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = RuntimeContext()
        self.interpreter = Interpreter(self.context)
        
        # Mock LLM resource
        self.mock_llm = MagicMock()
        self.mock_llm.query = AsyncMock(return_value=BaseResponse(
            success=True,
            content={"choices": [{"message": {"content": "This is a mock reasoning response"}}]}
        ))
        self.mock_llm.initialize = AsyncMock()
        
        # Register the mock LLM resource
        self.context.register_resource("llm", self.mock_llm)
        
        # Set up private variables
        self.context.set("private.test_variable", "test value")
        self.context.set("private.temperature_data", [20.5, 21.0, 22.5, 23.0])
        self.context.set("private.equipment", {"type": "sensor", "status": "operational"})

    def test_reason_ast_creation(self):
        """Test that the reason AST node is created correctly."""
        # Create a ReasonStatement directly
        prompt = LiteralExpression(literal=Literal(value="What is the answer?"))
        reason_stmt = ReasonStatement(prompt=prompt)
        
        # Check the properties
        self.assertEqual(reason_stmt.prompt, prompt)
        self.assertIsNone(reason_stmt.target)
        self.assertIsNone(reason_stmt.context)
        self.assertIsNone(reason_stmt.options)

    def test_reason_parsing_basic(self):
        """Test basic parsing of reason statements."""
        code = 'reason("What is the meaning of life?")'
        result = parse(code)
        
        # Verify parsing succeeded
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.program.statements), 1)
        
        # Check that it's a ReasonStatement
        stmt = result.program.statements[0]
        self.assertIsInstance(stmt, ReasonStatement)
        
        # Check the properties
        self.assertIsNone(stmt.target)
        self.assertIsNone(stmt.context)
        self.assertIsNone(stmt.options)

    def test_reason_parsing_with_assignment(self):
        """Test parsing reason statements with assignment."""
        code = 'answer = reason("What is the meaning of life?")'
        result = parse(code)
        
        # Verify parsing succeeded
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.program.statements), 1)
        
        # Check that it's a ReasonStatement
        stmt = result.program.statements[0]
        self.assertIsInstance(stmt, ReasonStatement)
        
        # Check the properties
        self.assertIsNotNone(stmt.target)
        self.assertEqual(stmt.target.name, "answer")
        self.assertIsNone(stmt.context)
        self.assertIsNone(stmt.options)

    def test_reason_parsing_with_context(self):
        """Test parsing reason statements with context."""
        code = 'analysis = reason("Analyze the data", context=temperature_data)'
        result = parse(code)
        
        # Verify parsing succeeded
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.program.statements), 1)
        
        # Check that it's a ReasonStatement
        stmt = result.program.statements[0]
        self.assertIsInstance(stmt, ReasonStatement)
        
        # Check the properties
        self.assertIsNotNone(stmt.target)
        self.assertEqual(stmt.target.name, "analysis")
        self.assertIsNotNone(stmt.context)
        self.assertEqual(len(stmt.context), 1)
        self.assertEqual(stmt.context[0].name, "temperature_data")

    def test_reason_parsing_with_context_list(self):
        """Test parsing reason statements with context list."""
        code = 'analysis = reason("Analyze the data", context=[temperature_data, equipment])'
        result = parse(code)
        
        # Verify parsing succeeded
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.program.statements), 1)
        
        # Check that it's a ReasonStatement
        stmt = result.program.statements[0]
        self.assertIsInstance(stmt, ReasonStatement)
        
        # Check the properties
        self.assertIsNotNone(stmt.target)
        self.assertEqual(stmt.target.name, "analysis")
        self.assertIsNotNone(stmt.context)
        self.assertEqual(len(stmt.context), 2)
        self.assertEqual(stmt.context[0].name, "temperature_data")
        self.assertEqual(stmt.context[1].name, "equipment")

    def test_reason_parsing_with_options(self):
        """Test parsing reason statements with options."""
        code = 'result = reason("Generate ideas", temperature=0.9, format="json")'
        result = parse(code)
        
        # Verify parsing succeeded
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.program.statements), 1)
        
        # Check that it's a ReasonStatement
        stmt = result.program.statements[0]
        self.assertIsInstance(stmt, ReasonStatement)
        
        # Check the properties
        self.assertIsNotNone(stmt.target)
        self.assertEqual(stmt.target.name, "result")
        self.assertIsNotNone(stmt.options)
        self.assertEqual(stmt.options["temperature"], 0.9)
        self.assertEqual(stmt.options["format"], "json")

    def test_reason_parsing_with_fstring(self):
        """Test parsing reason statements with f-strings."""
        code = 'analysis = reason(f"Analyze the data: {temperature_data}")'
        result = parse(code)
        
        # Verify parsing succeeded
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.program.statements), 1)
        
        # Check that it's a ReasonStatement
        stmt = result.program.statements[0]
        self.assertIsInstance(stmt, ReasonStatement)
        
        # Check that the prompt is a valid expression
        self.assertIsNotNone(stmt.prompt)

    def test_reason_execution(self):
        """Test execution of reason statements."""
        # Create a simple program with a reason statement
        code = 'answer = reason("What is the meaning of life?")'
        result = parse(code)
        
        # Execute the program with the real implementation (auto-uses visitor pattern)
        self.interpreter.execute_program(result)
        
        # Check that the LLM was called
        self.mock_llm.query.assert_called_once()
        
        # Check that the result was stored in the context
        self.assertEqual(self.context.get("private.answer"), "This is a mock reasoning response")

    def test_reason_with_context(self):
        """Test execution of reason statements with context."""
        # Create a program with a reason statement using context
        code = 'analysis = reason("Analyze the data", context=temperature_data)'
        result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(result)
        
        # Check that the LLM was called
        self.mock_llm.query.assert_called()
        
        # Check that the result was stored in the context
        self.assertEqual(self.context.get("private.analysis"), 
                         "This is a mock reasoning response")

    def test_reason_with_options(self):
        """Test execution of reason statements with options."""
        # Create a program with a reason statement using options
        code = 'ideas = reason("Generate ideas", temperature=0.9, format="json")'
        result = parse(code)
        
        # Execute the program
        self.interpreter.execute_program(result)
        
        # Check that the LLM was called
        self.mock_llm.query.assert_called()
        
        # Check that the options were passed in the LLM call
        calls = self.mock_llm.query.call_args_list
        for call in calls:
            # BaseRequest's arguments should have temperature
            if hasattr(call.args[0], 'arguments') and 'temperature' in call.args[0].arguments:
                args = call.args[0].arguments
                self.assertIn('temperature', args)
                self.assertEqual(args['temperature'], 0.9)
        
        # Check that the result was stored in the context
        self.assertEqual(self.context.get("private.ideas"), 
                         "This is a mock reasoning response")

    def test_perform_reasoning(self):
        """Test the _perform_reasoning method directly."""
        # Create a test prompt and context variables
        prompt = "What do you think about this data?"
        context_vars = ["test_variable"]
        options = {"temperature": 0.5, "format": "text"}
        
        # Set up an event loop for the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Call the method directly using run_until_complete
        result = loop.run_until_complete(
            self.interpreter._perform_reasoning(prompt, context_vars, options)
        )
        
        # Check that the LLM.query was called
        self.mock_llm.query.assert_called_once()
        
        # Check that the result is what we expect (from our mock)
        self.assertEqual(result, "This is a mock reasoning response")


if __name__ == "__main__":
    unittest.main()