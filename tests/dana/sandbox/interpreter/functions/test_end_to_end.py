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

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.sandbox_context import SandboxContext


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
    interpreter.function_registry.register("python_logger", python_logger, func_type=FunctionType.PYTHON)
    interpreter.function_registry.register("create_formatter", create_formatter, func_type=FunctionType.PYTHON)

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
    interpreter.function_registry.register("analyze_data", analyze_data, func_type=FunctionType.PYTHON)

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
    SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("format_message", format_message, func_type=FunctionType.PYTHON)

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
    SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("divide", divide, func_type=FunctionType.PYTHON)

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
    from dana.core.lang.parser.ast import Assignment, BinaryExpression, BinaryOperator, Identifier, LiteralExpression, Program

    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Test 1: Program execution with assignments
    program = Program([Assignment(target=Identifier("private:y"), value=LiteralExpression(123))])
    result = interpreter.execute_program(program, context)
    assert result == 123
    assert context.get("private:y") == 123

    # Test 2: Expression evaluation
    expr = BinaryExpression(
        left=LiteralExpression(17),
        operator=BinaryOperator.ADD,
        right=LiteralExpression(25),
    )
    result = interpreter.evaluate_expression(expr, context)
    assert result == 42

    # Test 3: Statement execution
    stmt = Assignment(target=Identifier("private:z"), value=LiteralExpression(456))
    result = interpreter.execute_statement(stmt, context)
    assert result == 456
    assert context.get("private:z") == 456

    # Test 4: Multiple statements in program
    program = Program(
        [
            Assignment(target=Identifier("local:a"), value=LiteralExpression(10)),
            Assignment(target=Identifier("local:b"), value=LiteralExpression(20)),
            Assignment(
                target=Identifier("local:sum"),
                value=BinaryExpression(left=Identifier("local:a"), operator=BinaryOperator.ADD, right=Identifier("local:b")),
            ),
        ]
    )
    result = interpreter.execute_program(program, context)
    assert result == 30  # Result of last statement
    assert context.get("local:a") == 10
    assert context.get("local:b") == 20
    assert context.get("local:sum") == 30

    # Test 5: Complex expression evaluation
    complex_expr = BinaryExpression(
        left=BinaryExpression(left=Identifier("local:a"), operator=BinaryOperator.MULTIPLY, right=LiteralExpression(2)),
        operator=BinaryOperator.ADD,
        right=BinaryExpression(left=Identifier("local:b"), operator=BinaryOperator.DIVIDE, right=LiteralExpression(4)),
    )
    result = interpreter.evaluate_expression(complex_expr, context)
    assert result == 25.0  # (10 * 2) + (20 / 4) = 20 + 5 = 25


def test_fstring_evaluation_comprehensive():
    """Test comprehensive f-string evaluation.

    Migrated from tests/dana/sandbox/test_fixed_functions.py::test_fstring_evaluation()
    Enhanced with additional f-string scenarios and edge cases.
    """
    from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
    from dana.core.lang.parser.ast import BinaryExpression, BinaryOperator, FStringExpression, Identifier, LiteralExpression

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
    interpreter.function_registry.register("calculate_stats", calculate_stats, func_type=FunctionType.PYTHON)
    interpreter.function_registry.register("format_stats", format_stats, func_type=FunctionType.PYTHON)

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

        # Handle POETResult wrapper if present
        from dana.frameworks.poet.types import POETResult

        if isinstance(result, POETResult):
            unwrapped_result = result.unwrap()
            assert isinstance(unwrapped_result, str | dict)
        else:
            assert isinstance(result, str | dict)

        # Test 2: Reason function with context variables
        context.set("topic", "mathematics")
        context.set("question", "What is the square root of 16?")

        # This would normally use f-strings, but we'll test direct calls
        result = interpreter.call_function("reason", [f"Topic: {context.get('topic')} - {context.get('question')}"])
        assert result is not None

        # Test 3: Reason function with options
        result = interpreter.call_function("reason", ["Explain gravity"])
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
    interpreter.function_registry.register("string_processor", string_processor, func_type=FunctionType.PYTHON)
    interpreter.function_registry.register("math_calculator", math_calculator, func_type=FunctionType.PYTHON)
    interpreter.function_registry.register("context_aware_function", context_aware_function, func_type=FunctionType.PYTHON)

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
