"""Tests for the DANA interpreter hooks.

This module contains tests for the hook system that allows extending the DANA
interpreter with custom behavior at key points in the execution process.
"""

import pytest

from dana.parser.dana_parser import DanaParser
from dana.sandbox.interpreter.hooks import (
    HookRegistry,
    HookType,
)
from dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return DanaParser()


@pytest.fixture
def context():
    """Create a runtime context for testing."""
    return SandboxContext()


def create_interpreter(context: SandboxContext) -> Interpreter:
    """Create an interpreter with the given context.

    Args:
        context: The runtime context to use

    Returns:
        An interpreter instance
    """
    return Interpreter.new(context)


def test_hook_registration():
    """Test registering and executing a hook."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define a test hook
    def test_hook(context):
        assert isinstance(context, dict)
        context["test"] = True

    # Register the hook
    HookRegistry.register(HookType.BEFORE_PROGRAM, test_hook)

    # Verify the hook is registered
    assert HookRegistry.has_hooks(HookType.BEFORE_PROGRAM)

    # Execute the hook
    context = {}
    HookRegistry.execute(HookType.BEFORE_PROGRAM, context)
    assert context["test"] is True

    # Clean up
    HookRegistry.clear()


def test_hook_unregistration():
    """Test unregistering a hook."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define a test hook
    def test_hook(context):
        pass

    # Register the hook
    HookRegistry.register(HookType.BEFORE_PROGRAM, test_hook)

    # Verify the hook is registered
    assert HookRegistry.has_hooks(HookType.BEFORE_PROGRAM)

    # Unregister the hook
    HookRegistry.unregister(HookType.BEFORE_PROGRAM, test_hook)

    # Verify the hook is no longer registered
    assert not HookRegistry.has_hooks(HookType.BEFORE_PROGRAM)

    # Clean up
    HookRegistry.clear()


def test_program_hooks():
    """Test program-level hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def before_program_hook(context):
        assert "program" in context
        context["before"] = True

    def after_program_hook(context):
        assert "program" in context
        context["after"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_PROGRAM, before_program_hook)
    HookRegistry.register(HookType.AFTER_PROGRAM, after_program_hook)

    # Execute the hooks
    context = {"program": "test"}
    HookRegistry.execute(HookType.BEFORE_PROGRAM, context)
    HookRegistry.execute(HookType.AFTER_PROGRAM, context)

    # Verify the hooks were executed
    assert context["before"] is True
    assert context["after"] is True

    # Clean up
    HookRegistry.clear()


def test_statement_hooks():
    """Test statement-level hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def before_statement_hook(context):
        assert "node" in context
        context["before"] = True

    def after_statement_hook(context):
        assert "node" in context
        context["after"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_STATEMENT, before_statement_hook)
    HookRegistry.register(HookType.AFTER_STATEMENT, after_statement_hook)

    # Execute the hooks
    context = {"node": "test"}
    HookRegistry.execute(HookType.BEFORE_STATEMENT, context)
    HookRegistry.execute(HookType.AFTER_STATEMENT, context)

    # Verify the hooks were executed
    assert context["before"] is True
    assert context["after"] is True

    # Clean up
    HookRegistry.clear()


def test_error_hooks():
    """Test error hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hook
    def error_hook(context):
        assert "error" in context
        context["handled"] = True

    # Register the hook
    HookRegistry.register(HookType.ON_ERROR, error_hook)

    # Execute the hook
    context = {"error": Exception("test")}
    HookRegistry.execute(HookType.ON_ERROR, context)

    # Verify the hook was executed
    assert context["handled"] is True

    # Clean up
    HookRegistry.clear()


def test_conditional_hooks():
    """Test conditional hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def before_conditional_hook(context):
        assert "node" in context
        context["before"] = True

    def after_conditional_hook(context):
        assert "node" in context
        assert "condition" in context
        context["after"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_CONDITIONAL, before_conditional_hook)
    HookRegistry.register(HookType.AFTER_CONDITIONAL, after_conditional_hook)

    # Execute the hooks
    context = {"node": "test", "condition": True}
    HookRegistry.execute(HookType.BEFORE_CONDITIONAL, context)
    HookRegistry.execute(HookType.AFTER_CONDITIONAL, context)

    # Verify the hooks were executed
    assert context["before"] is True
    assert context["after"] is True

    # Clean up
    HookRegistry.clear()


def test_loop_hooks():
    """Test loop hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def before_loop_hook(context):
        assert "node" in context
        context["before"] = True

    def after_loop_hook(context):
        assert "node" in context
        assert "iterations" in context
        context["after"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_LOOP, before_loop_hook)
    HookRegistry.register(HookType.AFTER_LOOP, after_loop_hook)

    # Execute the hooks
    context = {"node": "test", "iterations": 5}
    HookRegistry.execute(HookType.BEFORE_LOOP, context)
    HookRegistry.execute(HookType.AFTER_LOOP, context)

    # Verify the hooks were executed
    assert context["before"] is True
    assert context["after"] is True

    # Clean up
    HookRegistry.clear()


def test_log_hooks():
    """Test log hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def before_log_hook(context):
        assert "node" in context
        context["before"] = True

    def after_log_hook(context):
        assert "node" in context
        assert "message" in context
        context["after"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_LOG, before_log_hook)
    HookRegistry.register(HookType.AFTER_LOG, after_log_hook)

    # Execute the hooks
    context = {"node": "test", "message": "test message"}
    HookRegistry.execute(HookType.BEFORE_LOG, context)
    HookRegistry.execute(HookType.AFTER_LOG, context)

    # Verify the hooks were executed
    assert context["before"] is True
    assert context["after"] is True

    # Clean up
    HookRegistry.clear()


def test_reason_hooks():
    """Test reason hooks."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def before_reason_hook(context):
        assert "node" in context
        context["before"] = True

    def after_reason_hook(context):
        assert "node" in context
        assert "result" in context
        context["after"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_REASON, before_reason_hook)
    HookRegistry.register(HookType.AFTER_REASON, after_reason_hook)

    # Execute the hooks
    context = {"node": "test", "result": "test result"}
    HookRegistry.execute(HookType.BEFORE_REASON, context)
    HookRegistry.execute(HookType.AFTER_REASON, context)

    # Verify the hooks were executed
    assert context["before"] is True
    assert context["after"] is True

    # Clean up
    HookRegistry.clear()


def test_multiple_hooks():
    """Test registering and executing multiple hooks for the same type."""
    # Clear any existing hooks
    HookRegistry.clear()

    # Define test hooks
    def hook1(context):
        context["hook1"] = True

    def hook2(context):
        context["hook2"] = True

    def hook3(context):
        context["hook3"] = True

    # Register the hooks
    HookRegistry.register(HookType.BEFORE_STATEMENT, hook1)
    HookRegistry.register(HookType.BEFORE_STATEMENT, hook2)
    HookRegistry.register(HookType.BEFORE_STATEMENT, hook3)

    # Execute the hooks
    context = {}
    HookRegistry.execute(HookType.BEFORE_STATEMENT, context)

    # Verify all hooks were executed
    assert context["hook1"] is True
    assert context["hook2"] is True
    assert context["hook3"] is True

    # Clean up
    HookRegistry.clear()
