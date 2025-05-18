import pytest

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.executor.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.executor.llm_integration import LLMIntegration
from opendxa.dana.sandbox.interpreter.executor.statement_executor import StatementExecutor
from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction, DanaRegistry
from opendxa.dana.sandbox.interpreter.functions.python_function import PythonFunction, PythonRegistry
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    AttributeAccess,
    BinaryExpression,
    BinaryOperator,
    DictLiteral,
    FStringExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    PrintStatement,
    Program,
    SubscriptExpression,
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
    # Setup DanaFunction
    class MockAST:
        pass

    class MockInterpreter:
        def __init__(self, context):
            pass

        def execute_program(self, ast):
            return "dana-called"

    monkeypatch.setitem(
        __import__("sys").modules, "opendxa.dana.sandbox.interpreter.interpreter", type("mod", (), {"Interpreter": MockInterpreter})
    )
    context = SandboxContext()
    cm = ContextManager(context)
    ee = ExpressionEvaluator(cm)
    llm = LLMIntegration(cm)
    se = StatementExecutor(cm, ee, llm)

    # 1. foo_registry() resolves to registry function if present
    DanaRegistry()._functions.clear()
    PythonRegistry()._functions.clear()
    DanaRegistry().register("foo_registry", DanaFunction(MockAST(), [], None))
    node = FunctionCall(name="foo_registry", args={})
    assert se._execute_method_or_variable_function(node) == "dana-called"
    # Now clear for next sub-case
    DanaRegistry()._functions.clear()
    PythonRegistry()._functions.clear()

    # 2. foo_local() falls back to local.foo_local if callable
    DanaRegistry()._functions.clear()
    PythonRegistry()._functions.clear()
    node = FunctionCall(name="foo_local", args={})
    context.set("local.foo_local", lambda: "local-called")
    assert se._execute_method_or_variable_function(node) == "local-called"
    context._state["local"].pop("foo_local")

    # 3. foo_missing() raises error if neither registry nor local.foo_missing exists
    DanaRegistry()._functions.clear()
    PythonRegistry()._functions.clear()
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
    llm = LLMIntegration(cm)
    se = StatementExecutor(cm, ee, llm)
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
    result = interpreter.execute_program(program, suppress_exceptions=False)
    assert context.get("private.y") == 123

    # Error case: invalid statement
    class Dummy:
        pass

    program = Program([Dummy()])
    with pytest.raises(Exception):
        interpreter.execute_program(program, suppress_exceptions=False)  # type: ignore


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
        cm.get_from_context("private.missing")


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
        interpreter.execute_program(program, suppress_exceptions=False)
