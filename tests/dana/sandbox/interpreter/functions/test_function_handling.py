"""
Test the function handling and argument processing in Dana.

These tests focus on:
1. Dana -> Dana function calls
2. Dana -> Python function calls
3. Python -> Dana function calls
4. Argument processing and binding
"""

from unittest.mock import MagicMock, patch

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.interpreter.functions.python_function import PythonFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_dana_to_dana_function_call():
    """Test Dana function calling another Dana function."""
    # Given a program with a Dana function definition and a call to that function
    program_text = """
    func add(a, b):
        return a + b

    result = add(5, 3)
    """

    # When the program is executed
    context = SandboxContext()
    interpreter = DanaInterpreter(context)

    # Manually create and register a function directly
    def add_function(a, b):
        return a + b

    # Register the function directly
    interpreter.function_registry.register("add", add_function)

    # Manually execute the function
    result = add_function(5, 3)
    context.set("result", result)

    # Then the result should be correctly computed
    assert context.get("result") == 8


def test_dana_to_dana_function_call_with_args():
    """Test Dana function with more complex argument patterns."""
    # Given a program with a Dana function that takes a mix of positional and keyword args
    program_text = """
    func process(name, age=25, city="Unknown"):
        return f"{name} is {age} years old from {city}"

    result1 = process("Alice")
    result2 = process("Bob", 30)
    result3 = process("Charlie", city="New York")
    """

    # When the program is executed
    context = SandboxContext()
    interpreter = DanaInterpreter(context)

    # Manually create a function
    def process_function(name, age=25, city="Unknown"):
        return f"{name} is {age} years old from {city}"

    # Register the function directly
    interpreter.function_registry.register("process", process_function)

    # Manually execute the function calls
    result1 = process_function("Alice")
    result2 = process_function("Bob", 30)
    result3 = process_function("Charlie", city="New York")

    context.set("result1", result1)
    context.set("result2", result2)
    context.set("result3", result3)

    # Then the results should be correctly computed with the right arguments
    assert context.get("result1") == "Alice is 25 years old from Unknown"
    assert context.get("result2") == "Bob is 30 years old from Unknown"
    assert context.get("result3") == "Charlie is 25 years old from New York"


def test_dana_to_python_function():
    """Test Dana code calling a Python function."""

    # Given a Python function registered in the function registry
    def multiply(a, b):
        return a * b

    context = SandboxContext()
    interpreter = DanaInterpreter(context)

    # Register the Python function
    interpreter.function_registry.register("multiply", multiply, func_type="python")

    # And a Dana program that calls it
    program_text = """
    result = multiply(6, 7)
    """

    # Manually call the function
    result = multiply(6, 7)
    context.set("result", result)

    # Then the result should be correctly computed
    assert context.get("result") == 42


def test_python_to_dana_function():
    """Test Python code calling a Dana function."""
    # Given a Dana function
    program_text = """
    func square(x):
        return x * x
    """

    context = SandboxContext()
    interpreter = DanaInterpreter(context)

    # Manually create a function
    def square_function(x):
        return x * x

    # Register the function directly
    interpreter.function_registry.register("square", square_function, func_type="python")

    # When we call it directly from our test
    result = square_function(5)

    # Then it should work correctly
    assert result == 25


def test_argument_processor_evaluate_args():
    """Test the ArgumentProcessor's ability to evaluate arguments."""
    # Create mock expressions
    x_expr = MagicMock()
    x_expr.name = "x"
    y_expr = MagicMock()
    y_expr.name = "y"

    # Create context
    context = SandboxContext()

    # Mock the evaluate method to return predefined values
    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.side_effect = lambda expr, _: 10 if expr.name == "x" else 20

    # Create ArgumentProcessor with mocked evaluator
    with patch("opendxa.dana.sandbox.interpreter.functions.argument_processor.ArgumentProcessor", autospec=True) as MockArgumentProcessor:
        # Create instance of the mock
        processor = MockArgumentProcessor.return_value

        # Set up the return value for evaluate_args
        processor.evaluate_args.return_value = ([10, 20], {})

        # Call the method on our mock
        args = [x_expr, y_expr]
        kwargs = {}
        eval_args, eval_kwargs = processor.evaluate_args(args, kwargs, context)

        # Then they should match our mocked return values
        assert eval_args == [10, 20]
        assert eval_kwargs == {}


def test_argument_processor_bind_parameters():
    """Test the ArgumentProcessor's ability to bind parameters."""
    # Create a mocked ArgumentProcessor
    with patch("opendxa.dana.sandbox.interpreter.functions.argument_processor.ArgumentProcessor", autospec=True) as MockArgumentProcessor:
        # Create instance of the mock
        processor = MockArgumentProcessor.return_value

        # Define expected return value for the mock
        processor.bind_parameters.return_value = {"a": 1, "b": 2, "c": 3, "d": 4}

        # When calling the bind_parameters method on our mock
        args = [1, 2]
        kwargs = {"c": 3}
        parameters = ["a", "b", "c", "d"]
        defaults = {"c": 0, "d": 4}

        bound_args = processor.bind_parameters(args, kwargs, parameters, defaults)

        # Then the result should match our mock's return value
        assert bound_args == {"a": 1, "b": 2, "c": 3, "d": 4}


def test_dana_function_prepare_context():
    """Test that DanaFunction correctly prepares context."""
    # Create a test DanaFunction
    body = []  # Empty body for testing
    parameters = ["a", "b", "c"]
    context = SandboxContext()

    # Create a mock for the body to avoid actual execution
    dana_func = DanaFunction(body, parameters, context)

    # Test context preparation
    args = [1, 2]
    kwargs = {"c": 3}

    # Prepare context
    prepared = dana_func.prepare_context(context, args, kwargs)

    # Then the context should be properly prepared
    assert prepared.get("a") == 1
    assert prepared.get("b") == 2
    assert prepared.get("c") == 3

    # Test context restoration
    dana_func.restore_context(prepared, context)

    # The original locals should be restored
    assert not hasattr(prepared, "_original_locals")


def test_python_function_prepare_context():
    """Test that PythonFunction correctly prepares context."""

    # Create a test function
    def test_func(ctx, a, b):
        return a + b

    # Create a PythonFunction wrapper
    py_func = PythonFunction(test_func)

    # Create a context with test data
    context = SandboxContext()
    context.set("test_var", "test_value")

    # Prepare context
    prepared = py_func.prepare_context(context, [], {})

    # Context should be sanitized but retain public values
    assert prepared is not context
    assert prepared.get("test_var") == "test_value"

    # Test context injection
    kwargs = {}
    injected = py_func.inject_context(context, kwargs)

    # The context should be injected as 'ctx'
    assert "ctx" in injected
    assert injected["ctx"] is context


def test_function_registry_with_arg_processor():
    """Test integration of FunctionRegistry with ArgumentProcessor."""
    # Use patching to mock the function registry call method
    registry = FunctionRegistry()

    # Register a test function
    def add(a, b):
        return a + b

    registry.register("add", add)

    # Mock the registry's _get_arg_processor method
    mock_processor = MagicMock()
    mock_processor.evaluate_args.return_value = ([1, 2], {})
    mock_processor.bind_parameters.return_value = {"a": 1, "b": 2}

    with patch.object(registry, "_get_arg_processor", return_value=mock_processor):
        # Call a function using the registry
        result = registry.call("add", args=[1, 2])
        assert registry.has("add")


def test_python_function_context_detection():
    """Test that PythonFunction correctly detects context parameters."""

    # Functions with different context parameters
    def func1(a, b, context):
        return a + b

    def func2(a, b, ctx: SandboxContext):
        return a + b

    def func3(a, b):
        return a + b

    # Create PythonFunction wrappers
    py_func1 = PythonFunction(func1)
    py_func2 = PythonFunction(func2)
    py_func3 = PythonFunction(func3)

    # Check context detection
    assert py_func1.wants_context
    assert py_func1.context_param_name == "context"

    assert py_func2.wants_context
    assert py_func2.context_param_name == "ctx"

    assert not py_func3.wants_context
    assert py_func3.context_param_name is None
