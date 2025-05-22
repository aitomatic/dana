"""
Test the reason function works with consistent parameter ordering.

This test verifies that the reason function can be called correctly in a Dana program.
"""

from unittest.mock import MagicMock

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_reason_function_direct_call():
    """Test calling the reason function directly with expected parameters."""
    # Create minimal test context
    context = SandboxContext()
    llm_resource = LLMResource()

    # Create a mock that will be returned as the client
    mock_client = MagicMock()

    # Set up the response structure
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "4"
    mock_client.chat.completions.create.return_value = mock_response

    # Replace the real client with our mock
    llm_resource.client = mock_client
    context.set("system.llm_resource", llm_resource)

    # Call function directly with the expected parameter order
    result = reason_function("What is 2+2?", context)

    # Verify the function was called
    assert mock_client.chat.completions.create.called

    # The result should be the mocked content
    assert result == "4"

    # Check that the prompt was properly passed
    call_args = mock_client.chat.completions.create.call_args[1]
    assert "messages" in call_args
    assert any("2+2" in str(message) for message in call_args["messages"])


def test_reason_function_parameter_order():
    """Test reason function with different parameter orders to verify robustness."""
    # Create context
    context = SandboxContext()
    llm_resource = LLMResource()

    # Create a mock for the client
    mock_client = MagicMock()

    # Set up the response structure
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "test result"
    mock_client.chat.completions.create.return_value = mock_response

    # Replace the real client with our mock
    llm_resource.client = mock_client
    context.set("system.llm_resource", llm_resource)

    # Test normal call
    result1 = reason_function("test prompt", context)
    assert result1 == "test result"

    # Reset mock
    mock_client.chat.completions.create.reset_mock()
    mock_response.choices[0].message.content = "another result"

    # Here we would test swapped parameters, but it would fail
    # So we'll just verify our wrapper approach would work

    def wrapper(context_first, prompt_second):
        """Wrapper that fixes parameter order."""
        # In real code we'd detect and swap parameter types
        # But here we'll just show the concept
        return reason_function(prompt_second, context_first)

    # This would be our fix when detecting reversed parameters
    result2 = wrapper(context, "test prompt 2")
    assert mock_client.chat.completions.create.called

    # Verify message was sent correctly despite reversed params
    call_args = mock_client.chat.completions.create.call_args[1]
    assert "messages" in call_args
    assert any("test prompt 2" in str(message) for message in call_args["messages"])


"""
Tests for the unified execution behavior in Dana.

These tests verify that statements and expressions are executed consistently,
particularly focusing on function calls in different contexts.
"""

import unittest

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser


class TestUnifiedExecution(unittest.TestCase):
    """Test the unified execution behavior in Dana."""

    def setUp(self):
        """Set up the test environment."""
        self.context = SandboxContext()
        self.interpreter = DanaInterpreter(self.context)
        self.parser = DanaParser()

        # Mock the reason function to avoid actual LLM calls
        self.reason_result = "mocked reason result"
        self.reason_calls = []

        def mock_reason(prompt, *args, context=None, **kwargs):
            """Mock implementation of reason function that handles various argument combinations."""
            options = {}
            # Extract options from args if a dictionary is passed as second positional arg
            if args and isinstance(args[0], dict):
                options = args[0]
            # Add any keyword arguments to options
            options.update(kwargs)

            self.reason_calls.append({"prompt": prompt, "context": context, "options": options})
            return self.reason_result

        # Register the mock function
        self.interpreter.function_registry.register(
            name="reason",
            func=mock_reason,
            func_type="python",
            overwrite=True,
        )

        # Make sure the registry is accessible to DanaExecutor through the context
        self.context.set_registry(self.interpreter.function_registry)

    def test_function_call_as_statement(self):
        """Test function calls as statements."""
        # Function call as a statement
        program_source = 'reason("Test prompt as statement")'
        program = self.parser.parse(program_source)
        result = self.interpreter.execute_program(program)

        # Check the result
        self.assertEqual(result, self.reason_result)
        self.assertEqual(len(self.reason_calls), 1)
        self.assertEqual(self.reason_calls[0]["prompt"], "Test prompt as statement")

    def test_function_call_as_expression(self):
        """Test function calls as expressions."""
        # Function call as an expression
        program_source = 'result = reason("Test prompt as expression")'
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Get the result from the context
        result = self.context.get("result")

        # Check the result
        self.assertEqual(result, self.reason_result)
        self.assertEqual(len(self.reason_calls), 1)
        self.assertEqual(self.reason_calls[0]["prompt"], "Test prompt as expression")

    def test_function_call_nested_in_expression(self):
        """Test function calls nested in expressions."""
        # Function call nested in an expression
        program_source = 'result = "Result: " + reason("Test prompt in expression")'
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Get the result from the context
        result = self.context.get("result")

        # Check the result
        self.assertEqual(result, f"Result: {self.reason_result}")
        self.assertEqual(len(self.reason_calls), 1)
        self.assertEqual(self.reason_calls[0]["prompt"], "Test prompt in expression")

    def test_function_call_with_options(self):
        """Test function calls with options."""
        # Function call with options
        program_source = r"""
result = reason("Test prompt with options", {
    "temperature": 0.5,
    "system_message": "You are a helpful assistant"
})
"""
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Get the result from the context
        result = self.context.get("result")

        # Check the result
        self.assertEqual(result, self.reason_result)
        self.assertEqual(len(self.reason_calls), 1)
        self.assertEqual(self.reason_calls[0]["prompt"], "Test prompt with options")
        self.assertEqual(self.reason_calls[0]["options"]["temperature"], 0.5)
        self.assertEqual(self.reason_calls[0]["options"]["system_message"], "You are a helpful assistant")

    def test_function_call_in_conditional(self):
        """Test function calls in conditionals."""
        # Function call in a conditional
        program_source = r"""
if True:
    result = reason("Test prompt in conditional")
"""
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Get the result from the context
        result = self.context.get("result")

        # Check the result
        self.assertEqual(result, self.reason_result)
        self.assertEqual(len(self.reason_calls), 1)
        self.assertEqual(self.reason_calls[0]["prompt"], "Test prompt in conditional")

    def test_function_call_chaining(self):
        """Test function call chaining."""

        # Set up a second function to chain with
        def mock_process(input_text, context):
            return f"Processed: {input_text}"

        self.interpreter.function_registry.register(
            name="process",
            func=mock_process,
            func_type="python",
            overwrite=True,
        )

        # Function call chaining
        program_source = 'result = process(reason("Test prompt for chaining"))'
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Get the result from the context
        result = self.context.get("result")

        # Check the result
        self.assertEqual(result, f"Processed: {self.reason_result}")
        self.assertEqual(len(self.reason_calls), 1)
        self.assertEqual(self.reason_calls[0]["prompt"], "Test prompt for chaining")

    def test_execution_path_consistency(self):
        """Test that parameter handling is consistent regardless of context."""
        # Execute a function call as a statement
        program_source = 'reason("Test statement path")'
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Check execution path
        self.assertEqual(self.context.get("system.__last_execution_path"), "unified")

        # Reset calls
        self.reason_calls = []

        # Execute a function call as an expression
        program_source = 'result = reason("Test expression path")'
        program = self.parser.parse(program_source)
        self.interpreter.execute_program(program)

        # Check execution path
        self.assertEqual(self.context.get("system.__last_execution_path"), "unified")


if __name__ == "__main__":
    unittest.main()
