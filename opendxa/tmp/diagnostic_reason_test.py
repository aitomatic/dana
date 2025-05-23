"""
Diagnostic test for the reason function to verify that it works in both regular test environment
and in REPL-style calls with LiteralExpression lists.
"""

import sys

from opendxa.dana.sandbox.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.executor.statement_executor import StatementExecutor
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.parser.ast import FunctionCall, LiteralExpression
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class MockLLMResource:
    """Mock LLM resource for testing."""

    def query_sync(self, request):
        """Mock implementation that returns a successful response with test content."""

        class MockResponse:
            success = True
            error = None
            content = "This is a test response from the LLM"

        return MockResponse()


def test_direct_reason_call():
    """Test calling reason_function directly."""
    # Create a sandbox context with a mock LLM resource
    context = SandboxContext()
    # Properly set the llm_resource in the system scope
    context.set("system.llm_resource", MockLLMResource())

    # Call the function directly with a string prompt
    result = reason_function("test prompt", context)
    assert result == "This is a test response from the LLM"

    # Verify the function works with a list of LiteralExpression
    mock_expr = LiteralExpression(value="test prompt from LiteralExpression")
    result = reason_function([mock_expr], context)
    assert result == "This is a test response from the LLM"


def test_via_expression_evaluator():
    """Test calling reason through the expression evaluator."""
    # Set up the context and evaluator
    context = SandboxContext()
    context.set("system.llm_resource", MockLLMResource())
    context_manager = ContextManager(context)
    registry = FunctionRegistry()

    # Register the reason function
    registry.register("reason", reason_function)

    # Create an expression evaluator with the function registry
    evaluator = ExpressionEvaluator(context_manager)
    evaluator.function_registry = registry

    # Create a function call node (similar to what parser would create)
    function_call = FunctionCall(name="reason", args={"__positional": [LiteralExpression(value="test prompt via evaluator")]})

    # Evaluate the function call
    result = evaluator.evaluate(function_call)
    assert result == "This is a test response from the LLM"

    # Test with local.reason (which should be redirected)
    function_call = FunctionCall(
        name="local.reason", args={"__positional": [LiteralExpression(value="test prompt with local.reason prefix")]}
    )

    result = evaluator.evaluate(function_call)
    assert result == "This is a test response from the LLM"


def test_via_statement_executor():
    """Test calling reason through the statement executor (similar to REPL)."""
    # Set up the context, evaluator, and executor
    context = SandboxContext()
    context.set("system.llm_resource", MockLLMResource())
    context_manager = ContextManager(context)
    registry = FunctionRegistry()

    # Register the reason function
    registry.register("reason", reason_function)

    # Create an expression evaluator with the function registry
    evaluator = ExpressionEvaluator(context_manager)
    evaluator.function_registry = registry

    # Create a statement executor
    executor = StatementExecutor(context_manager, evaluator)
    executor.function_registry = registry

    # Create a function call node
    function_call = FunctionCall(name="reason", args={"__positional": [LiteralExpression(value="test prompt via executor")]})

    # Execute the function call
    result = executor.execute_function_call(function_call)
    assert result == "This is a test response from the LLM"

    # Test with local.reason (which should be redirected)
    function_call = FunctionCall(
        name="local.reason", args={"__positional": [LiteralExpression(value="test prompt with local.reason via executor")]}
    )

    result = executor.execute_function_call(function_call)
    assert result == "This is a test response from the LLM"


def test_via_statement_executor_with_list_args():
    """Test calling reason with list arguments (simulating REPL literal list behavior)."""
    # Set up the context, evaluator, and executor
    context = SandboxContext()
    context.set("system.llm_resource", MockLLMResource())
    context_manager = ContextManager(context)
    registry = FunctionRegistry()

    # Register the reason function
    registry.register("reason", reason_function)

    # Create an expression evaluator with the function registry
    evaluator = ExpressionEvaluator(context_manager)
    evaluator.function_registry = registry

    # Create a statement executor
    executor = StatementExecutor(context_manager, evaluator)
    executor.function_registry = registry

    # Create LiteralExpression for the argument
    lit_expr = LiteralExpression(value="test prompt as list arg")

    # Create a function call node with a list of LiteralExpressions as we'd see in REPL
    function_call = FunctionCall(name="reason", args={"__positional": [[lit_expr]]})  # Double list to simulate REPL behavior

    # Execute the function call
    result = executor.execute_function_call(function_call)
    assert result == "This is a test response from the LLM"


if __name__ == "__main__":
    test_direct_reason_call()
    test_via_expression_evaluator()
    test_via_statement_executor()
    test_via_statement_executor_with_list_args()
    print("All tests completed successfully!")
    sys.exit(0)
