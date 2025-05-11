"""Tests for the DANA interpreter hooks.

This module contains tests for the hook system that allows extending the DANA
interpreter with custom behavior at key points in the execution process.
"""

import pytest

from opendxa.dana.language.parser import GrammarParser
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.hooks import (
    HookType,
    clear_hooks,
    execute_hook,
    has_hooks,
    register_hook,
)
from opendxa.dana.runtime.interpreter import Interpreter


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


@pytest.fixture
def context():
    """Create a runtime context for testing."""
    return RuntimeContext()


def create_interpreter(context: RuntimeContext) -> Interpreter:
    """Create an interpreter with the given context.

    Args:
        context: The runtime context to use

    Returns:
        An interpreter instance
    """
    return Interpreter(context)


def test_hook_registry_basics():
    """Test basic hook registry functionality."""
    # Clean up any existing hooks
    clear_hooks()

    # Test hook registration and execution
    executed = False

    def test_hook(context):
        nonlocal executed
        executed = True

    # Register a hook
    register_hook(HookType.BEFORE_PROGRAM, test_hook)

    # Check that the hook is registered
    assert has_hooks(HookType.BEFORE_PROGRAM)

    # Execute the hook
    execute_hook(HookType.BEFORE_PROGRAM, {})

    # Check that the hook was executed
    assert executed


def test_global_hook_registry():
    """Test that the global hook registry is shared."""
    # Clean up any existing hooks
    clear_hooks()

    # Test hook registration and execution
    executed = False

    def test_hook(context):
        nonlocal executed
        executed = True

    # Register a hook
    register_hook(HookType.BEFORE_PROGRAM, test_hook)

    # Create a new interpreter
    interpreter = create_interpreter(RuntimeContext())

    # Execute a program to trigger the hook
    parser = GrammarParser()
    interpreter.execute_program(parser.parse("private.a = 42"))

    # Check that the hook was executed
    assert executed


def test_program_hooks(parser, context):
    """Test program-level hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"before_program": 0, "after_program": 0}

    def before_program_hook(context):
        executed["before_program"] += 1

    def after_program_hook(context):
        executed["after_program"] += 1

    # Register hooks
    register_hook(HookType.BEFORE_PROGRAM, before_program_hook)
    register_hook(HookType.AFTER_PROGRAM, after_program_hook)

    # Execute a program
    result = parser.parse("private.a = 42")
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_program"] == 1
    assert executed["after_program"] == 1


def test_statement_hooks(parser, context):
    """Test statement-level hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"before_statement": 0, "after_statement": 0}

    def before_statement_hook(context):
        executed["before_statement"] += 1

    def after_statement_hook(context):
        executed["after_statement"] += 1

    # Register hooks
    register_hook(HookType.BEFORE_STATEMENT, before_statement_hook)
    register_hook(HookType.AFTER_STATEMENT, after_statement_hook)

    # Execute a program with multiple statements
    result = parser.parse("private.a = 42")
    interpreter.execute_program(result)

    # Check that hooks were executed for each statement
    assert executed["before_statement"] == 1
    assert executed["after_statement"] == 1


def test_error_hooks(parser, context):
    """Test error hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"on_error": 0, "error": None}

    def error_hook(context):
        executed["on_error"] += 1
        if "error" in context:
            executed["error"] = context["error"]

    # Register hook
    register_hook(HookType.ON_ERROR, error_hook)

    # Execute a program that will cause an error
    result = parser.parse("private.a = undefined_variable")
    try:
        interpreter.execute_program(result)
    except Exception:
        pass

    # Check that the error hook was executed
    assert executed["on_error"] == 1
    assert executed["error"] is not None


@pytest.mark.skip(reason="Conditional hooks test disabled due to parser limitations.")
def test_conditional_hooks(parser, context):
    """Test conditional statement hooks."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"before_conditional": 0, "after_conditional": 0, "condition_value": None}

    def before_conditional_hook(context):
        executed["before_conditional"] += 1

    def after_conditional_hook(context):
        executed["after_conditional"] += 1
        assert "condition" in context
        executed["condition_value"] = context["condition"]

    # Register hooks
    register_hook(HookType.BEFORE_CONDITIONAL, before_conditional_hook)
    register_hook(HookType.AFTER_CONDITIONAL, after_conditional_hook)

    # Execute a program with a conditional
    result = parser.parse("if private.a > 0: private.b = 42 else: private.b = 0")
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_conditional"] == 1
    assert executed["after_conditional"] == 1
    assert executed["condition_value"] is not None


@pytest.mark.skip(reason="Loop hooks test disabled due to parser limitations.")
def test_loop_hooks(parser, context):
    """Test loop statement hooks."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"before_loop": 0, "after_loop": 0, "iterations": None}

    def before_loop_hook(context):
        executed["before_loop"] += 1

    def after_loop_hook(context):
        executed["after_loop"] += 1
        assert "iterations" in context
        executed["iterations"] = context["iterations"]

    # Register hooks
    register_hook(HookType.BEFORE_LOOP, before_loop_hook)
    register_hook(HookType.AFTER_LOOP, after_loop_hook)

    # Execute a program with a loop
    result = parser.parse("private.i = 0; while private.i < 3: private.i = private.i + 1")
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_loop"] == 1
    assert executed["after_loop"] == 1
    assert executed["iterations"] is not None


def test_log_hooks(parser, context):
    """Test log statement hooks."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"before_log": 0, "after_log": 0, "message": None}

    def before_log_hook(context):
        executed["before_log"] += 1

    def after_log_hook(context):
        executed["after_log"] += 1
        assert "message" in context
        executed["message"] = context["message"]

    # Register hooks
    register_hook(HookType.BEFORE_LOG, before_log_hook)
    register_hook(HookType.AFTER_LOG, after_log_hook)

    # Execute a program with a log statement
    result = parser.parse('log("test message")')
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_log"] == 1
    assert executed["after_log"] == 1
    assert executed["message"] == "test message"


def test_reason_hooks(parser, context):
    """Test reason statement hooks."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    executed = {"before_reason": 0, "after_reason": 0, "result": None}

    def before_reason_hook(context):
        executed["before_reason"] += 1

    def after_reason_hook(context):
        executed["after_reason"] += 1
        assert "result" in context
        executed["result"] = context["result"]

    # Register hooks
    register_hook(HookType.BEFORE_REASON, before_reason_hook)
    register_hook(HookType.AFTER_REASON, after_reason_hook)

    # Execute a program with a reason statement
    result = parser.parse('reason("What is 2 + 2?")')
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_reason"] == 1
    assert executed["after_reason"] == 1
    assert executed["result"] is not None


def test_multiple_hooks(parser, context):
    """Test that multiple hooks of the same type are executed in order."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    interpreter = create_interpreter(context)

    execution_order = []

    def hook1(context):
        execution_order.append(1)

    def hook2(context):
        execution_order.append(2)

    def hook3(context):
        execution_order.append(3)

    # Register multiple hooks
    register_hook(HookType.BEFORE_STATEMENT, hook1)
    register_hook(HookType.BEFORE_STATEMENT, hook2)
    register_hook(HookType.BEFORE_STATEMENT, hook3)

    # Execute a program
    result = parser.parse("private.a = 42")
    interpreter.execute_program(result)

    # Check that hooks were executed in order
    assert execution_order == [1, 2, 3]
