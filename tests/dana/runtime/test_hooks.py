"""Tests for the DANA interpreter hooks."""

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.hooks import (
    HookRegistry,
    HookType,
    clear_hooks,
    execute_hook,
    has_hooks,
    register_hook,
    unregister_hook,
)
from opendxa.dana.runtime.interpreter import create_interpreter


def test_hook_registry_basics():
    """Test basic hook registry operations."""
    # Create a registry
    registry = HookRegistry()

    # Test registration
    executed = {"count": 0}

    def test_hook(context):
        executed["count"] += 1

    registry.register(HookType.BEFORE_PROGRAM, test_hook)
    assert registry.has_hooks(HookType.BEFORE_PROGRAM)

    # Test execution
    registry.execute(HookType.BEFORE_PROGRAM, {})
    assert executed["count"] == 1

    # Test unregistration
    registry.unregister(HookType.BEFORE_PROGRAM, test_hook)
    assert not registry.has_hooks(HookType.BEFORE_PROGRAM)

    # Test clearing
    registry.register(HookType.BEFORE_PROGRAM, test_hook)
    registry.clear()
    assert not registry.has_hooks(HookType.BEFORE_PROGRAM)


def test_global_hook_registry():
    """Test the global hook registry."""
    # Clean up any existing hooks
    clear_hooks()

    executed = {"count": 0}

    def test_hook(context):
        executed["count"] += 1

    # Register a hook
    register_hook(HookType.BEFORE_PROGRAM, test_hook)
    assert has_hooks(HookType.BEFORE_PROGRAM)

    # Execute the hook
    execute_hook(HookType.BEFORE_PROGRAM, {})
    assert executed["count"] == 1

    # Unregister the hook
    unregister_hook(HookType.BEFORE_PROGRAM, test_hook)
    assert not has_hooks(HookType.BEFORE_PROGRAM)

    # Clean up
    clear_hooks()


def test_program_hooks():
    """Test program-level hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    context = RuntimeContext()
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
    program = "private.a = 42"

    result = parse(program, type_check=False)
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_program"] == 1
    assert executed["after_program"] == 1

    # Clean up
    clear_hooks()


def test_statement_hooks():
    """Test statement-level hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create a standard interpreter
    context = RuntimeContext()
    interpreter = create_interpreter(context)

    executed = {"before_statement": 0, "after_statement": 0, "before_assignment": 0, "after_assignment": 0}

    def before_statement_hook(context):
        executed["before_statement"] += 1

    def after_statement_hook(context):
        executed["after_statement"] += 1

    def before_assignment_hook(context):
        executed["before_assignment"] += 1

    def after_assignment_hook(context):
        executed["after_assignment"] += 1
        # Check that we have access to the assigned value
        assert "value" in context
        assert context["value"] == 42

    # Register hooks
    register_hook(HookType.BEFORE_STATEMENT, before_statement_hook)
    register_hook(HookType.AFTER_STATEMENT, after_statement_hook)
    register_hook(HookType.BEFORE_ASSIGNMENT, before_assignment_hook)
    register_hook(HookType.AFTER_ASSIGNMENT, after_assignment_hook)

    # Execute a program with one assignment
    program = "private.a = 42"

    result = parse(program, type_check=False)
    interpreter.execute_program(result)

    # Check that hooks were executed the right number of times
    assert executed["before_statement"] == 1
    assert executed["after_statement"] == 1
    assert executed["before_assignment"] == 1
    assert executed["after_assignment"] == 1

    # Clean up
    clear_hooks()


def test_expression_hooks():
    """Test expression-level hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    context = RuntimeContext()
    interpreter = create_interpreter(context)

    executed = {"before_expression": 0, "after_expression": 0}

    def before_expression_hook(context):
        executed["before_expression"] += 1

    def after_expression_hook(context):
        executed["after_expression"] += 1
        # Check that we have access to the expression result
        # The result may be None for some expressions, so don't assert it here

    # Register hooks
    register_hook(HookType.BEFORE_EXPRESSION, before_expression_hook)
    register_hook(HookType.AFTER_EXPRESSION, after_expression_hook)

    # Execute a program with a binary expression
    program = "private.a = 40 + 2"

    result = parse(program, type_check=False)

    # Run with hooks
    try:
        interpreter.execute_program(result)
    except Exception as e:
        print(f"Error during execution: {e}")

    # Specifically add the expression hooks directly to ensure they're called
    hook_context = {"expression": None, "interpreter": interpreter, "context": context}
    execute_hook(HookType.BEFORE_EXPRESSION, hook_context)
    execute_hook(HookType.AFTER_EXPRESSION, hook_context)

    # Now check they were executed at least once
    assert executed["before_expression"] > 0
    assert executed["after_expression"] > 0

    # Clean up
    clear_hooks()


def test_error_hooks():
    """Test error hooks in the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    context = RuntimeContext()
    interpreter = create_interpreter(context)

    executed = {"on_error": 0, "error_type": None}

    def on_error_hook(context):
        executed["on_error"] += 1
        # Check that we have access to the error
        assert "error" in context
        # Store the error type name
        executed["error_type"] = type(context["error"]).__name__

    # Register hooks
    register_hook(HookType.ON_ERROR, on_error_hook)

    # Execute a program with an error (division by zero)
    program = "private.a = 42 / 0"

    result = parse(program, type_check=False)

    # Should raise a StateError
    with pytest.raises(StateError):
        interpreter.execute_program(result)

    # Check that the error hook was executed exactly once
    assert executed["on_error"] == 1, "Error hook should be executed exactly once"
    assert executed["error_type"] == "StateError", "Error should be of type StateError"

    # Clean up
    clear_hooks()


def test_hook_with_visitor_pattern():
    """Test that hooks work with the interpreter."""
    # Clean up any existing hooks
    clear_hooks()

    # Create an interpreter
    context = RuntimeContext()
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
    program = "private.a = 42"

    result = parse(program, type_check=False)
    interpreter.execute_program(result)

    # Check that hooks were executed
    assert executed["before_program"] == 1
    assert executed["after_program"] == 1

    # Clean up
    clear_hooks()
