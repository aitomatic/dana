import pytest

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.executor.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.executor.llm_integration import LLMIntegration
from opendxa.dana.sandbox.interpreter.executor.statement_executor import StatementExecutor
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionMetadata, FunctionRegistry
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    FunctionCall,
    Identifier,
    LiteralExpression,
    PrintStatement,
    Program,
)
from opendxa.dana.sandbox.sandbox_context import SandboxContext


# --- PythonFunction and PythonRegistry tests ---
def test_python_function_registry_and_call():
    def add(x, y):
        return x + y

    py_func = PythonFunction(lambda x, y: x + y)
    reg = PythonRegistry()
    reg.register("add", py_func)
    assert reg.has("add")
    func = reg.get("add")
    assert func.call(None, 2, 3) == 5


# --- DanaFunction and DanaRegistry tests ---
def test_dana_function_registry_and_call(monkeypatch):
    # Mock AST and interpreter for test
    class MockAST:
        pass

    class MockInterpreter:
        def __init__(self, context):
            self.context = context

        def execute_program(self, ast):
            return "dana-called"

    monkeypatch.setitem(
        __import__("sys").modules, "opendxa.dana.sandbox.interpreter.interpreter", type("mod", (), {"Interpreter": MockInterpreter})
    )
    dana_func = DanaFunction(MockAST(), [], None)
    reg = DanaRegistry()
    reg.register("dana_func", dana_func)
    assert reg.has("dana_func")
    func = reg.get("dana_func")
    assert func.call(SandboxContext()) == "dana-called"


# --- Registry list and error handling ---
def test_registry_list_and_missing():
    PythonRegistry()._functions.clear()  # Ensure test isolation
    reg = PythonRegistry()
    reg.register("foo", PythonFunction(lambda: 1))
    assert reg.list() == ["foo"]
    assert reg.has("foo")
    with pytest.raises(KeyError):
        reg.get("bar")


# --- Integration: StatementExecutor function call logic ---
def test_statement_executor_function_resolution(monkeypatch):
    # Setup mock function that will be called
    def mock_dana_function(*args, **kwargs):
        return "dana-called"

    class MockInterpreter:
        def __init__(self, context):
            self.context = context
            self.function_registry = FunctionRegistry()  # Create registry in interpreter

        def execute_program(self, ast):
            return "dana-called"

    monkeypatch.setitem(
        __import__("sys").modules, "opendxa.dana.sandbox.interpreter.interpreter", type("mod", (), {"Interpreter": MockInterpreter})
    )

    context = SandboxContext()
    cm = ContextManager(context)
    ee = ExpressionEvaluator(cm)  # No longer pass registry here
    llm = LLMIntegration()  # Initialize without arguments
    se = StatementExecutor(cm, ee, llm)

    # Create mock interpreter and set it
    mock_interpreter = MockInterpreter(context)
    ee.interpreter = mock_interpreter
    se.interpreter = mock_interpreter

    # 1. foo_registry() resolves to registry function if present
    mock_interpreter.function_registry.register(
        "foo_registry", mock_dana_function, func_type="dana", metadata=FunctionMetadata(context_aware=True)  # Use simple function
    )
    node = FunctionCall(name="foo_registry", args={})
    assert se._execute_method_or_variable_function(node) == "dana-called"

    # 2. foo_local() falls back to local.foo_local if callable
    node = FunctionCall(name="foo_local", args={})
    context.set("local.foo_local", lambda: "local-called")
    assert se._execute_method_or_variable_function(node) == "local-called"
    context._state["local"].pop("foo_local")

    # 3. foo_missing() raises error if neither registry nor local.foo_missing exists
    node = FunctionCall(name="foo_missing", args={})
    with pytest.raises(SandboxError, match="Function or variable 'foo_missing' not found"):
        se._execute_method_or_variable_function(node)

    # 4. local:foo_direct() always calls local context
    context.set("local.foo_direct", lambda x: x * 2)
    node = FunctionCall(name="local:foo_direct", args={"0": LiteralExpression(7)})
    assert se._execute_method_or_variable_function(node) == 14
    context._state["local"].pop("foo_direct")


def test_python_registry_register_and_get():
    reg = PythonRegistry()
    reg._functions.clear()  # Ensure isolation
    reg.register("test_func", PythonFunction(lambda: 123))
    assert reg.has("test_func")
    assert reg.get("test_func").call(None) == 123
    with pytest.raises(KeyError):
        reg.get("missing_func")


def test_dana_registry_register_and_get(monkeypatch):
    class MockAST:
        pass

    class MockInterpreter:
        def __init__(self, context):
            self.context = context

        def execute_program(self, ast):
            return "dana-called"

    monkeypatch.setitem(
        __import__("sys").modules, "opendxa.dana.sandbox.interpreter.interpreter", type("mod", (), {"Interpreter": MockInterpreter})
    )
    reg = DanaRegistry()
    reg._functions.clear()
    dana_func = DanaFunction(MockAST(), [], None)
    reg.register("dana_func", dana_func)
    assert reg.has("dana_func")
    assert reg.get("dana_func").call(SandboxContext()) == "dana-called"
    with pytest.raises(KeyError):
        reg.get("missing_func")


def test_expression_evaluator_literal_and_binary():
    context = SandboxContext()
    cm = ContextManager(context)
    evaluator = ExpressionEvaluator(cm)
    # Literal
    assert evaluator.evaluate(LiteralExpression(42)) == 42
    # Binary
    expr = BinaryExpression(left=LiteralExpression(2), operator=BinaryOperator.ADD, right=LiteralExpression(3))
    assert evaluator.evaluate(expr) == 5

    # Error case: unsupported node
    class Dummy:
        pass

    with pytest.raises(Exception):
        evaluator.evaluate(Dummy())


def test_statement_executor_assignment_and_print(capsys):
    context = SandboxContext()
    cm = ContextManager(context)
    ee = ExpressionEvaluator(cm)
    llm = LLMIntegration()  # Initialize without arguments
    se = StatementExecutor(cm, ee, llm)

    # Create mock interpreter and set it
    class MockInterpreter:
        def __init__(self, context):
            self.context = context
            self.function_registry = FunctionRegistry()

    mock_interpreter = MockInterpreter(context)
    ee.interpreter = mock_interpreter
    se.interpreter = mock_interpreter

    # Assignment
    stmt = Assignment(target=Identifier("private.x"), value=LiteralExpression(99))
    se.execute(stmt)
    assert context.get("private.x") == 99
    # Print
    stmt = PrintStatement(message=LiteralExpression("hello"))
    se.execute(stmt)
    out, _ = capsys.readouterr()
    assert "hello" in out

    # Error case: unsupported statement
    class Dummy:
        pass

    with pytest.raises(Exception):
        se.execute(Dummy())  # type: ignore


def test_interpreter_init_and_execute():
    context = SandboxContext()
    interpreter = Interpreter(context)
    program = Program([Assignment(target=Identifier("private.y"), value=LiteralExpression(123))])
    result = interpreter.execute_program(program)  # Remove suppress_exceptions
    assert context.get("private.y") == 123

    # Error case: invalid statement
    class Dummy:
        pass

    program = Program([Dummy()])
    with pytest.raises(Exception):
        interpreter.execute_program(program)  # Remove suppress_exceptions


def test_expression_evaluator_fstring_attribute_subscript():
    context = SandboxContext()
    cm = ContextManager(context)
    evaluator = ExpressionEvaluator(cm)
    # F-string
    fstring = FStringExpression(parts=["foo", LiteralExpression(42)])
    assert evaluator.evaluate(fstring) == "foo42"
    # Attribute access
    attr = AttributeAccess(object=DictLiteral(items=[(LiteralExpression("x"), LiteralExpression(1))]), attribute="x")
    assert evaluator.evaluate(attr) == 1
    # Subscript
    sub = SubscriptExpression(object=LiteralExpression([10, 20]), index=LiteralExpression(1))
    assert evaluator.evaluate(sub) == 20


def test_context_manager_missing_variable():
    context = SandboxContext()
    cm = ContextManager(context)
    with pytest.raises(Exception):
        cm.get_from_scope("private.missing")


def test_interpreter_error_hook(monkeypatch):
    context = SandboxContext()
    interpreter = Interpreter(context)
    from opendxa.dana.sandbox.parser.ast import Program

    # Patch HookRegistry to simulate ON_ERROR hook
    class DummyHookRegistry:
        @staticmethod
        def has_hooks(hook_type):
            return hook_type == "ON_ERROR"

        @staticmethod
        def execute(hook_type, context):
            context["error_handled"] = True

    monkeypatch.setattr("opendxa.dana.sandbox.interpreter.hooks.HookRegistry", DummyHookRegistry)

    class Dummy:
        pass

    program = Program([Dummy()])
    with pytest.raises(Exception):
        interpreter.execute_program(program)


def test_register_and_call_python_function():
    registry = FunctionRegistry()

    def py_add(ctx, a, b):
        return a + b

    registry.register("add", py_add, func_type="python")
    result = registry.call("add", args=[2, 3], context={})  # Provide empty context
    assert result == 5


def test_register_and_call_python_function_with_namespace():
    registry = FunctionRegistry()

    def py_mul(ctx, a, b):
        return a * b

    registry.register("mul", py_mul, namespace="math", func_type="python")
    result = registry.call("mul", args=[4, 5], context={}, namespace="math")  # Provide empty context
    assert result == 20


def test_register_and_call_dana_function():
    registry = FunctionRegistry()

    def dana_double(ctx, x):
        return x * 2

    registry.register("double", dana_double, func_type="dana")
    result = registry.call("double", args=[7], context={})  # Provide empty context
    assert result == 14


def test_register_and_call_dana_function_with_namespace():
    registry = FunctionRegistry()

    def dana_triple(ctx, x):
        return x * 3

    registry.register("triple", dana_triple, namespace="util", func_type="dana")
    result = registry.call("triple", args=[6], context={}, namespace="util")  # Provide empty context
    assert result == 18


# New tests for enhanced FunctionRegistry


def test_function_registry_basic_operations():
    """Test basic registry operations."""
    registry = FunctionRegistry()

    # Test registration
    def test_func(x: int) -> int:
        return x * 2

    registry.register("double", test_func)
    assert registry.has("double")
    assert not registry.has("triple")

    # Test resolution
    func, func_type, metadata = registry.resolve("double")
    assert func == test_func
    assert func_type == "dana"  # default type
    assert isinstance(metadata, FunctionMetadata)

    # Test listing
    assert "double" in registry.list()

    # Test calling
    result = registry.call("double", args=[5])
    assert result == 10


def test_function_registry_namespaces():
    """Test namespace support."""
    registry = FunctionRegistry()

    # Register functions in different namespaces
    def add(a, b):
        return a + b

    def sub(a, b):
        return a - b

    registry.register("calc", add, namespace="math")
    registry.register("calc", sub, namespace="other")  # Same name, different namespace

    # Test resolution in different namespaces
    assert registry.call("calc", args=[5, 3], namespace="math") == 8
    assert registry.call("calc", args=[5, 3], namespace="other") == 2

    # Test listing by namespace
    assert "calc" in registry.list(namespace="math")
    assert "calc" in registry.list(namespace="other")


def test_function_registry_metadata():
    """Test metadata handling."""
    registry = FunctionRegistry()

    def context_aware_func(ctx, x):
        return f"Context: {ctx}, Value: {x}"

    # Test with explicit metadata
    metadata = FunctionMetadata(context_aware=True, is_public=True, doc="Test function", source_file="test.py")
    registry.register("test", context_aware_func, metadata=metadata)

    # Verify metadata
    retrieved_metadata = registry.get_metadata("test")
    assert retrieved_metadata.context_aware
    assert retrieved_metadata.is_public
    assert retrieved_metadata.doc == "Test function"
    assert retrieved_metadata.source_file == "test.py"


def test_function_registry_python_context_detection():
    """Test automatic context awareness detection for Python functions."""
    registry = FunctionRegistry()

    def with_context(ctx, x):
        return x

    def without_context(x):
        return x

    registry.register("with_ctx", with_context, func_type="python")
    registry.register("without_ctx", without_context, func_type="python")

    # Check auto-detected metadata
    assert registry.get_metadata("with_ctx").context_aware
    assert not registry.get_metadata("without_ctx").context_aware


def test_function_registry_overwrite_protection():
    """Test function overwrite protection."""
    registry = FunctionRegistry()

    def func1(x):
        return x

    def func2(x):
        return x * 2

    registry.register("test", func1)

    # Should raise error when trying to overwrite without flag
    with pytest.raises(ValueError):
        registry.register("test", func2)

    # Should succeed with overwrite flag
    registry.register("test", func2, overwrite=True)
    result = registry.call("test", args=[5])
    assert result == 10  # Should use func2


def test_function_registry_context_injection():
    """Test context injection behavior."""
    registry = FunctionRegistry()
    test_context = {"test": "context"}

    def context_func(ctx, x):
        assert ctx == test_context
        return x * 2

    # Register with explicit context awareness
    registry.register("test", context_func, metadata=FunctionMetadata(context_aware=True))

    # Test calling with context
    result = registry.call("test", args=[5], context=test_context)
    assert result == 10


def test_function_registry_error_handling():
    """Test error handling scenarios."""
    registry = FunctionRegistry()

    # Test resolving non-existent function
    with pytest.raises(KeyError):
        registry.resolve("nonexistent")

    # Test calling non-existent function
    with pytest.raises(KeyError):
        registry.call("nonexistent")

    # Test invalid argument count
    def strict_func(x, y):  # Function that requires exactly 2 arguments
        return x + y

    registry.register("strict", strict_func)

    # Should raise TypeError when passing wrong number of arguments
    with pytest.raises(TypeError, match="Error calling function 'strict'"):
        registry.call("strict", args=[1])  # Missing second argument
