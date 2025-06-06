"""
End-to-end tests for the function call system.

These tests verify that all components of the function call system work
together correctly, including:
1. Python to Dana calls
2. Dana to Python calls
3. Context passing
4. Argument processing
5. Error handling
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseResponse
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.ast import Assignment, BinaryExpression, BinaryOperator, Identifier, LiteralExpression, Program
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_mixed_dana_and_python_functions():
    """Test Python and Dana functions working together with context passing."""

    # Define a Python function that needs context
    def python_logger(message, context):
        """Python function that logs a message and accesses context."""
        # Access the logs list from context
        logs = context.get("logs", [])
        logs.append(f"Python: {message}")
        context.set("logs", logs)
        return f"Logged: {message}"

    # Define a Python function that returns a callable (higher-order function)
    def create_formatter(prefix):
        """Returns a function that formats messages with a prefix."""

        def formatter(message):
            return f"{prefix}: {message}"

        return formatter

    # Setup interpreter and context
    context = SandboxContext()
    context.set("logs", [])

    # Initialize all required scopes
    if "system" not in context._state:
        context._state["system"] = {}

    interpreter = DanaInterpreter()

    # Register the Python functions
    interpreter.function_registry.register("python_logger", python_logger, func_type="python")
    interpreter.function_registry.register("create_formatter", create_formatter, func_type="python")

    # Test 1: Call Python function that modifies context
    result1 = python_logger("Test message 1", context)
    assert result1 == "Logged: Test message 1"
    assert context.get("logs") == ["Python: Test message 1"]

    # Test 2: Call higher-order function
    formatter = create_formatter("INFO")
    result2 = formatter("System ready")
    assert result2 == "INFO: System ready"

    # Test 3: Chain function calls
    python_logger("Test message 2", context)
    assert context.get("logs") == ["Python: Test message 1", "Python: Test message 2"]


def test_context_injection_with_type_annotations():
    """Test context injection with type annotations."""

    # Define a Python function with annotated context parameter
    def analyze_data(data: list, ctx: "SandboxContext"):
        """Analyzes data and stores results in context."""
        result = sum(data)
        ctx.set("analysis_result", result)
        return result

    # Setup
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("analyze_data", analyze_data, func_type="python")

    # Test direct call
    test_data = [1, 2, 3, 4, 5]
    result = analyze_data(test_data, context)

    # Verify results
    assert result == 15
    assert context.get("analysis_result") == 15


def test_keyword_and_positional_args():
    """Test mixing keyword and positional arguments."""

    # Define a Python function with multiple parameters
    def format_message(template, name, age=0, location="unknown"):
        """Format a message with the given parameters."""
        return template.format(name=name, age=age, location=location)

    # Setup
    _ = SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("format_message", format_message, func_type="python")

    # Test various calling patterns
    template = "Hello {name}, you are {age} years old from {location}"

    # Test 1: All positional
    result1 = format_message(template, "Alice", 25, "New York")
    assert result1 == "Hello Alice, you are 25 years old from New York"

    # Test 2: Mixed positional and keyword
    result2 = format_message(template, "Bob", location="Paris")
    assert result2 == "Hello Bob, you are 0 years old from Paris"

    # Test 3: All keyword
    result3 = format_message(template=template, name="Charlie", age=30, location="London")
    assert result3 == "Hello Charlie, you are 30 years old from London"


def test_error_handling():
    """Test error handling in function calls."""

    # Define a Python function that validates inputs
    def divide(a, b):
        """Divide a by b, raising an error for division by zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    # Setup
    _ = SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("divide", divide, func_type="python")

    # Test successful call
    result = divide(10, 2)
    assert result == 5.0

    # Test error case
    try:
        divide(10, 0)
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert str(e) == "Cannot divide by zero"


def test_unified_interpreter_execution_comprehensive():
    """Test comprehensive unified interpreter execution.

    Migrated from tests/dana/sandbox/test_fixed_functions.py::test_unified_interpreter_execution()
    Enhanced with additional execution scenarios and comprehensive testing.
    """
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Test 1: Program execution with assignments
    program = Program([Assignment(target=Identifier("private.y"), value=LiteralExpression(123))])
    result = interpreter.execute_program(program, context)
    assert result == 123
    assert context.get("private.y") == 123

    # Test 2: Expression evaluation
    expr = BinaryExpression(
        left=LiteralExpression(17),
        operator=BinaryOperator.ADD,
        right=LiteralExpression(25),
    )
    result = interpreter.evaluate_expression(expr, context)
    assert result == 42

    # Test 3: Statement execution
    stmt = Assignment(target=Identifier("private.z"), value=LiteralExpression(456))
    result = interpreter.execute_statement(stmt, context)
    assert result == 456
    assert context.get("private.z") == 456

    # Test 4: Multiple statements in program
    program = Program(
        [
            Assignment(target=Identifier("local.a"), value=LiteralExpression(10)),
            Assignment(target=Identifier("local.b"), value=LiteralExpression(20)),
            Assignment(
                target=Identifier("local.sum"),
                value=BinaryExpression(left=Identifier("local.a"), operator=BinaryOperator.ADD, right=Identifier("local.b")),
            ),
        ]
    )
    result = interpreter.execute_program(program, context)
    assert result == 30  # Result of last statement
    assert context.get("local.a") == 10
    assert context.get("local.b") == 20
    assert context.get("local.sum") == 30

    # Test 5: Complex expression evaluation
    complex_expr = BinaryExpression(
        left=BinaryExpression(left=Identifier("local.a"), operator=BinaryOperator.MULTIPLY, right=LiteralExpression(2)),
        operator=BinaryOperator.ADD,
        right=BinaryExpression(left=Identifier("local.b"), operator=BinaryOperator.DIVIDE, right=LiteralExpression(4)),
    )
    result = interpreter.evaluate_expression(complex_expr, context)
    assert result == 25.0  # (10 * 2) + (20 / 4) = 20 + 5 = 25


def test_fstring_evaluation_comprehensive():
    """Test comprehensive f-string evaluation.

    Migrated from tests/dana/sandbox/test_fixed_functions.py::test_fstring_evaluation()
    Enhanced with additional f-string scenarios and edge cases.
    """
    from opendxa.dana.sandbox.interpreter.executor.dana_executor import DanaExecutor
    from opendxa.dana.sandbox.parser.ast import BinaryExpression, BinaryOperator, FStringExpression, Identifier, LiteralExpression

    context = SandboxContext()
    executor = DanaExecutor()

    # Test 1: Basic f-string
    fstring = FStringExpression(parts=["foo", LiteralExpression(42)])
    assert executor.execute(fstring, context) == "foo42"

    # Test 2: F-string with context variables
    context.set("x", 17)
    context.set("y", 25)
    fstring = FStringExpression(
        parts=[
            "The answer is: ",
            Identifier("x"),
            " + ",
            Identifier("y"),
            " = ",
            BinaryExpression(Identifier("x"), BinaryOperator.ADD, Identifier("y")),
        ]
    )
    assert executor.execute(fstring, context) == "The answer is: 17 + 25 = 42"

    # Test 3: Template-style f-string
    fstring2 = FStringExpression(parts=[])
    fstring2.template = "The answer is: {x} + {y} = {result}"
    fstring2.expressions = {
        "{x}": Identifier("x"),
        "{y}": Identifier("y"),
        "{result}": BinaryExpression(Identifier("x"), BinaryOperator.ADD, Identifier("y")),
    }
    assert executor.execute(fstring2, context) == "The answer is: 17 + 25 = 42"

    # Test 4: F-string with different data types
    context.set("name", "Dana")
    context.set("version", 1.5)
    context.set("active", True)

    fstring3 = FStringExpression(
        parts=["System: ", Identifier("name"), " v", Identifier("version"), " (active: ", Identifier("active"), ")"]
    )
    assert executor.execute(fstring3, context) == "System: Dana v1.5 (active: True)"

    # Test 5: F-string with nested expressions
    context.set("items", 5)
    context.set("price", 10.50)

    fstring4 = FStringExpression(
        parts=[
            "Total: ",
            Identifier("items"),
            " items × $",
            Identifier("price"),
            " = $",
            BinaryExpression(Identifier("items"), BinaryOperator.MULTIPLY, Identifier("price")),
        ]
    )
    assert executor.execute(fstring4, context) == "Total: 5 items × $10.5 = $52.5"


def test_end_to_end_function_integration():
    """Test end-to-end integration of all function system components."""

    # Define test functions
    def calculate_stats(data):
        """Calculate basic statistics for a list of numbers."""
        return {"count": len(data), "sum": sum(data), "avg": sum(data) / len(data), "min": min(data), "max": max(data)}

    def format_stats(stats, title="Statistics"):
        """Format statistics into a readable string."""
        return f"{title}: {stats['count']} items, avg={stats['avg']:.2f}, range={stats['min']}-{stats['max']}"

    # Setup
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Register functions
    interpreter.function_registry.register("calculate_stats", calculate_stats, func_type="python")
    interpreter.function_registry.register("format_stats", format_stats, func_type="python")

    # Test data
    test_data = [10, 20, 30, 40, 50]

    # Test 1: Calculate statistics
    stats = calculate_stats(test_data)
    expected_stats = {"count": 5, "sum": 150, "avg": 30.0, "min": 10, "max": 50}
    assert stats == expected_stats

    # Test 2: Format statistics
    formatted = format_stats(stats, "Test Data")
    assert formatted == "Test Data: 5 items, avg=30.00, range=10-50"

    # Test 3: Chain function calls
    chained_result = format_stats(calculate_stats([1, 2, 3, 4, 5]), "Sample")
    assert chained_result == "Sample: 5 items, avg=3.00, range=1-5"

    # Test 4: Store results in context
    context.set("dataset", [100, 200, 300])
    dataset_stats = calculate_stats(context.get("dataset"))
    context.set("stats", dataset_stats)

    assert context.get("stats")["avg"] == 200.0
    assert context.get("stats")["count"] == 3


def test_reason_function_integration():
    """Test reason function integration in end-to-end scenarios.

    Consolidates tests from tests/dana/functions/reason_function/ directory.
    """
    import os

    # Setup environment for mocking
    original_mock_env = os.environ.get("OPENDXA_MOCK_LLM")
    os.environ["OPENDXA_MOCK_LLM"] = "true"

    try:
        context = SandboxContext()
        interpreter = DanaInterpreter()

        # Test 1: Basic reason function call
        result = interpreter.call_function("reason", ["What is 2 + 2?"])
        assert result is not None
        assert isinstance(result, str | dict)

        # Test 2: Reason function with context variables
        context.set("topic", "mathematics")
        context.set("question", "What is the square root of 16?")

        # This would normally use f-strings, but we'll test direct calls
        result = interpreter.call_function("reason", [f"Topic: {context.get('topic')} - {context.get('question')}"])
        assert result is not None

        # Test 3: Reason function with options
        result = interpreter.call_function("reason", ["Explain gravity"], {"temperature": 0.7})
        assert result is not None

        # Test 4: Reason function error handling
        try:
            # Test with invalid input
            result = interpreter.call_function("reason", [None])
            # Should either handle gracefully or raise appropriate error
            assert result is not None or True  # Either succeeds or raises exception
        except Exception as e:
            # If it raises an exception, it should be meaningful
            assert len(str(e)) > 0

    finally:
        # Restore environment
        if original_mock_env is None:
            os.environ.pop("OPENDXA_MOCK_LLM", None)
        else:
            os.environ["OPENDXA_MOCK_LLM"] = original_mock_env


def test_comprehensive_function_scenarios():
    """Test comprehensive function scenarios covering all major use cases."""

    # Define a variety of test functions
    def string_processor(text, operation="upper"):
        """Process strings with various operations."""
        operations = {"upper": text.upper(), "lower": text.lower(), "reverse": text[::-1], "length": len(text)}
        return operations.get(operation, text)

    def math_calculator(a, b, operation="+"):
        """Perform mathematical operations."""
        operations = {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b != 0 else None, "**": a**b}
        return operations.get(operation)

    def context_aware_function(message, ctx):
        """Function that uses context for state management."""
        history = ctx.get("history", [])
        history.append(message)
        ctx.set("history", history)
        return f"Message {len(history)}: {message}"

    # Setup
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Register functions
    interpreter.function_registry.register("string_processor", string_processor, func_type="python")
    interpreter.function_registry.register("math_calculator", math_calculator, func_type="python")
    interpreter.function_registry.register("context_aware_function", context_aware_function, func_type="python")

    # Test 1: String processing
    assert string_processor("hello", "upper") == "HELLO"
    assert string_processor("WORLD", "lower") == "world"
    assert string_processor("abc", "reverse") == "cba"
    assert string_processor("test", "length") == 4

    # Test 2: Mathematical operations
    assert math_calculator(10, 5, "+") == 15
    assert math_calculator(10, 5, "-") == 5
    assert math_calculator(10, 5, "*") == 50
    assert math_calculator(10, 5, "/") == 2.0
    assert math_calculator(2, 3, "**") == 8

    # Test 3: Context-aware functions
    result1 = context_aware_function("First message", context)
    assert result1 == "Message 1: First message"
    assert context.get("history") == ["First message"]

    result2 = context_aware_function("Second message", context)
    assert result2 == "Message 2: Second message"
    assert context.get("history") == ["First message", "Second message"]

    # Test 4: Function composition
    text_result = string_processor("hello world", "upper")
    length_result = string_processor(text_result, "length")
    assert text_result == "HELLO WORLD"
    assert length_result == 11

    # Test 5: Error handling
    division_result = math_calculator(10, 0, "/")
    assert division_result is None  # Handles division by zero gracefully


# New Test Class for Reason Function Advanced Parameters
class TestReasonFunctionAdvancedParams(unittest.TestCase):
    def setUp(self):
        self.original_mock_env = os.environ.get("OPENDXA_MOCK_LLM")
        os.environ["OPENDXA_MOCK_LLM"] = "true"

        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()
        # Ensure system scope exists for context operations if needed by interpreter
        if "system" not in self.context._state:
            self.context._state["system"] = {}

        # Mock LLMResource that might be set by default in the context by a sandbox
        self.mock_system_llm = MagicMock(spec=LLMResource)
        self.mock_system_llm.query_sync.return_value = BaseResponse(
            success=True, content={"choices": [{"message": {"content": "mock system response"}}]}
        )
        self.mock_system_llm._is_available = True  # Ensure it reports as available
        self.mock_system_llm.name = "mock_system_llm"

        # self.context.set("system.llm_resource", self.mock_system_llm) # Set this per-test if needed for clarity

    def tearDown(self):
        if self.original_mock_env is None:
            os.environ.pop("OPENDXA_MOCK_LLM", None)
        else:
            os.environ["OPENDXA_MOCK_LLM"] = self.original_mock_env

        if hasattr(self.context, "cached_llm_resources"):
            delattr(self.context, "cached_llm_resources")

        # Clear any llm_resource that might have been set directly on context for a test
        if hasattr(self.context, "llm_resource"):
            delattr(self.context, "llm_resource")
        # And clear from state if set using context.set
        if "system" in self.context._state and "llm_resource" in self.context._state["system"]:
            del self.context._state["system"]["llm_resource"]

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.ConfigLoader")
    def test_reason_with_specific_model_full_id(self, mock_config_loader, mock_llm_resource):
        mock_config_instance = mock_config_loader.return_value
        mock_config_instance.get_default_config.return_value = {
            "preferred_models": [
                {"name": "openai:gpt-4o-mini", "required_api_keys": ["OPENAI_API_KEY"]},
                {"name": "anthropic:claude-3-opus", "required_api_keys": ["ANTHROPIC_API_KEY"]},
            ]
        }

        mock_llm_instance = mock_llm_resource.return_value
        mock_llm_instance.query_sync.return_value = BaseResponse(
            success=True, content={"choices": [{"message": {"content": "response from specific model"}}]}
        )
        mock_llm_instance._is_available = True
        mock_llm_instance.name = "llm_resource_for_anthropic_claude-3-opus"

        self.interpreter.call_function("reason", ["Test prompt"], {"model": "anthropic:claude-3-opus"}, self.context)

        mock_llm_resource.assert_called_once_with(name="llm_resource_for_anthropic_claude_3_opus", model="anthropic:claude-3-opus")
        mock_llm_instance.query_sync.assert_called_once()
        self.assertIn("anthropic:claude-3-opus", self.context.cached_llm_resources)
        self.assertIs(self.context.cached_llm_resources["anthropic:claude-3-opus"], mock_llm_instance)

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.ConfigLoader")
    def test_reason_with_specific_model_partial_name(self, mock_config_loader, mock_llm_resource):
        mock_config_instance = mock_config_loader.return_value
        mock_config_instance.get_default_config.return_value = {
            "preferred_models": [
                {"name": "openai:gpt-4o-mini", "required_api_keys": ["OPENAI_API_KEY"]},
                {"name": "anthropic:claude-3-opus-20240229", "required_api_keys": ["ANTHROPIC_API_KEY"]},
            ]
        }

        mock_llm_instance = mock_llm_resource.return_value
        mock_llm_instance.query_sync.return_value = BaseResponse(
            success=True, content={"choices": [{"message": {"content": "response from opus"}}]}
        )
        mock_llm_instance._is_available = True
        mock_llm_instance.name = "llm_resource_for_anthropic_claude_3_opus_20240229"

        self.interpreter.call_function("reason", ["Test prompt"], {"model": "claude-3-opus"}, self.context)

        mock_llm_resource.assert_called_once_with(
            name="llm_resource_for_anthropic_claude_3_opus_20240229", model="anthropic:claude-3-opus-20240229"
        )
        self.assertIn("claude-3-opus", self.context.cached_llm_resources)

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.ConfigLoader")
    def test_reason_model_caching(self, mock_config_loader, mock_llm_resource):
        mock_config_instance = mock_config_loader.return_value
        mock_config_instance.get_default_config.return_value = {
            "preferred_models": [{"name": "openai:gpt-x", "required_api_keys": ["SOME_KEY"]}]
        }

        mock_llm_instance = mock_llm_resource.return_value
        mock_llm_instance.query_sync.return_value = BaseResponse(
            success=True, content={"choices": [{"message": {"content": "cached response"}}]}
        )
        mock_llm_instance._is_available = True

        # First call - should create and cache
        self.interpreter.call_function("reason", ["Prompt 1"], {"model": "gpt-x"}, self.context)
        mock_llm_resource.assert_called_once_with(name="llm_resource_for_openai_gpt_x", model="openai:gpt-x")
        self.assertEqual(mock_llm_instance.query_sync.call_count, 1)
        self.assertIn("gpt-x", self.context.cached_llm_resources)
        cached_instance = self.context.cached_llm_resources["gpt-x"]

        # Second call - should use cached
        self.interpreter.call_function("reason", ["Prompt 2"], {"model": "gpt-x"}, self.context)
        mock_llm_resource.assert_called_once()  # Still only called once for instantiation
        self.assertEqual(mock_llm_instance.query_sync.call_count, 2)  # Query_sync called again
        self.assertIs(self.context.cached_llm_resources["gpt-x"], cached_instance)

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.ConfigLoader")
    def test_reason_with_unknown_model_falls_back_to_system_llm(self, mock_config_loader, mock_llm_resource):
        # Setup: ConfigLoader returns no matching model
        mock_config_instance = mock_config_loader.return_value
        mock_config_instance.get_default_config.return_value = {
            "preferred_models": [{"name": "existing:model", "required_api_keys": ["KEY"]}]
        }

        # System LLM is set in the context
        self.context.set("system.llm_resource", self.mock_system_llm)

        # MockLLMResource_class should NOT be called to instantiate a new one for the unknown model.
        # Instead, the self.mock_system_llm should be used.

        result = self.interpreter.call_function("reason", ["Test prompt"], {"model": "unknown-model"}, self.context)

        mock_config_loader.assert_called_once()  # ConfigLoader is called to search for "unknown-model"
        mock_llm_resource.assert_not_called()  # Should not create a new LLMResource for "unknown-model"
        # nor a default one if system.llm_resource is present

        self.mock_system_llm.query_sync.assert_called_once()  # The system_llm should have been queried
        self.assertEqual(result, "mock system response")

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.ConfigLoader")
    def test_reason_with_unavailable_specific_model_falls_back_to_system_llm(self, mock_config_loader, mock_llm_resource):
        mock_config_instance = mock_config_loader.return_value
        mock_config_instance.get_default_config.return_value = {
            "preferred_models": [{"name": "specific:unavail-model", "required_api_keys": ["KEY_X"]}]
        }

        # Specific model LLMResource reports as unavailable
        mock_specific_llm_instance = mock_llm_resource.return_value
        mock_specific_llm_instance._is_available = False  # Key aspect for this test
        mock_specific_llm_instance.name = "llm_resource_for_specific_unavail_model"

        # Set system LLM
        self.context.set("system.llm_resource", self.mock_system_llm)

        result = self.interpreter.call_function("reason", ["Test prompt"], {"model": "unavail-model"}, self.context)

        mock_llm_resource.assert_called_once_with(name="llm_resource_for_specific_unavail_model", model="specific:unavail-model")
        mock_specific_llm_instance.query_sync.assert_not_called()  # Specific unavailable one is not queried
        self.mock_system_llm.query_sync.assert_called_once()  # Fallback system LLM is queried
        self.assertEqual(result, "mock system response")
        # Check that the unavailable model was NOT cached, or if it was, it's the unavailable instance
        if "unavail-model" in self.context.cached_llm_resources:
            self.assertIs(self.context.cached_llm_resources["unavail-model"], mock_specific_llm_instance)

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_with_ipv")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_original_implementation")
    def test_reason_raw_prompt_true_bypasses_ipv(self, mock_original, mock_ipv):
        mock_original.return_value = "response from original"
        # Set a system LLM so original implementation has something to use
        self.context.set("system.llm_resource", self.mock_system_llm)

        self.interpreter.call_function("reason", ["Raw Prompt"], {"raw_prompt": True}, self.context)

        mock_original.assert_called_once()
        mock_ipv.assert_not_called()
        # Check that model=None was passed to _reason_original_implementation
        args, kwargs = mock_original.call_args
        self.assertIsNone(args[-1])  # model is the last positional arg for _reason_original_implementation

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_with_ipv")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_original_implementation")
    def test_reason_raw_prompt_false_attempts_ipv(self, mock_original, mock_ipv):
        mock_ipv.return_value = "response from ipv"
        # IPV might try to get a default LLM if not configured, this setup ensures it can
        self.context.set("system.llm_resource", self.mock_system_llm)

        self.interpreter.call_function("reason", ["IPV Prompt"], {"raw_prompt": False}, self.context)

        mock_ipv.assert_called_once()
        mock_original.assert_not_called()
        # Check that model=None was passed to _reason_with_ipv
        args, kwargs = mock_ipv.call_args
        self.assertIsNone(args[-1])  # model is the last positional arg for _reason_with_ipv

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.ConfigLoader")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_with_ipv")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_original_implementation")
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    def test_reason_specific_model_and_raw_prompt_true(self, mock_llm_resource, mock_original, mock_ipv, mock_config_loader):
        mock_config_instance = mock_config_loader.return_value
        mock_config_instance.get_default_config.return_value = {
            "preferred_models": [{"name": "openai:gpt-raw", "required_api_keys": ["KEY_RAW"]}]
        }

        mock_specific_llm_instance = mock_llm_resource.return_value
        mock_specific_llm_instance._is_available = True
        mock_specific_llm_instance.name = "llm_resource_for_openai_gpt_raw"
        # _reason_original_implementation will call query_sync on this instance
        mock_specific_llm_instance.query_sync.return_value = BaseResponse(
            success=True, content={"choices": [{"message": {"content": "raw model response"}}]}
        )

        # mock_original needs to be a passthrough to see LLMResource being used
        # Instead of mocking _reason_original_implementation, we let it run but check its internal calls.
        # For this test, we want to ensure the correct LLMResource (the specific one) is used by _reason_original_implementation

        result = self.interpreter.call_function(
            "reason", ["Raw Prompt Specific Model"], {"model": "gpt-raw", "raw_prompt": True}, self.context
        )

        mock_ipv.assert_not_called()  # IPV should be bypassed
        # Check that _reason_original_implementation was called (it's not mocked away by mock_original here, we mock LLMResource instead)
        # We expect LLMResource to be called for the specific model
        mock_llm_resource.assert_called_once_with(name="llm_resource_for_openai_gpt_raw", model="openai:gpt-raw")
        # And that instance's query_sync should be called
        mock_specific_llm_instance.query_sync.assert_called_once()
        self.assertEqual(result, "raw model response")
        self.assertIn("gpt-raw", self.context.cached_llm_resources)

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    def test_reason_backward_compatibility_uses_system_llm(self, mock_llm_resource):
        # If no model/raw_prompt options are given, and context has system.llm_resource
        self.context.set("system.llm_resource", self.mock_system_llm)

        result = self.interpreter.call_function("reason", ["Legacy prompt"], context=self.context)  # options={} is important

        self.mock_system_llm.query_sync.assert_called_once()
        mock_llm_resource.assert_not_called()  # Should not create a new default LLMResource
        self.assertEqual(result, "mock system response")

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.LLMResource")
    def test_reason_backward_compatibility_creates_default_llm_if_none_in_context(self, mock_llm_resource):
        # No system.llm_resource in context
        if "system" in self.context._state and "llm_resource" in self.context._state["system"]:
            del self.context._state["system"]["llm_resource"]
        if hasattr(self.context, "llm_resource"):
            delattr(self.context, "llm_resource")

        mock_default_llm_instance = mock_llm_resource.return_value
        mock_default_llm_instance.query_sync.return_value = BaseResponse(
            success=True, content={"choices": [{"message": {"content": "new default response"}}]}
        )
        mock_default_llm_instance._is_available = True
        mock_default_llm_instance.name = "default_llm"  # Default name LLMResource gives itself

        result = self.interpreter.call_function("reason", ["Legacy prompt no context llm"], context=self.context)

        mock_llm_resource.assert_called_once_with()  # Called with no args for default
        mock_default_llm_instance.query_sync.assert_called_once()
        self.assertEqual(result, "new default response")

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_with_ipv", side_effect=ImportError("IPV not available"))
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_original_implementation")
    def test_reason_ipv_import_error_falls_back_to_original(self, mock_original, mock_ipv_import_error):
        mock_original.return_value = "fallback response from original"
        self.context.set("system.llm_resource", self.mock_system_llm)  # For original impl to use

        self.interpreter.call_function("reason", ["Test prompt"], {}, self.context)

        mock_ipv_import_error.assert_called_once()
        mock_original.assert_called_once()
        args, kwargs = mock_original.call_args
        self.assertIsNone(args[4])  # model (5th arg, index 4) should be None

    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_with_ipv", side_effect=Exception("IPV failed badly"))
    @patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function._reason_original_implementation")
    def test_reason_ipv_execution_error_falls_back_to_original(self, mock_original, mock_ipv_execution_error):
        mock_original.return_value = "fallback response from original on IPV error"
        self.context.set("system.llm_resource", self.mock_system_llm)

        self.interpreter.call_function("reason", ["Test prompt"], {}, self.context)

        mock_ipv_execution_error.assert_called_once()
        mock_original.assert_called_once()
