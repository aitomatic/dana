"""Tests for nested conditionals in DANA."""

from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter


def test_nested_conditionals():
    """Test that nested conditionals work correctly."""
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Set up a program with nested conditionals
    context.set("private.outer", True)
    context.set("private.inner", True)
    context.set("private.result", "initial")

    program = """
    if private.outer:
        private.result = "outer"
        if private.inner:
            private.result = "inner"
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check that the innermost conditional was reached
    assert context.get("private.result") == "inner"

    # Now try with the inner condition false
    # Create a fresh context and interpreter to avoid state issues
    context = RuntimeContext()
    interpreter = Interpreter(context)

    context.set("private.outer", True)
    context.set("private.inner", False)
    context.set("private.result", "initial")

    program = """
    if private.outer:
        private.result = "outer"
        if private.inner:
            private.result = "inner"
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check that the outer conditional was reached but not the inner
    assert context.get("private.result") == "outer"

    # Now try with the outer condition false
    # Create a fresh context and interpreter to avoid state issues
    context = RuntimeContext()
    interpreter = Interpreter(context)

    context.set("private.outer", False)
    context.set("private.inner", True)
    context.set("private.result", "initial")

    program = """
    if private.outer:
        private.result = "outer"
        if private.inner:
            private.result = "inner"
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check that neither conditional was reached
    assert context.get("private.result") == "initial"


def test_multiple_nested_conditionals():
    """Test that multiple levels of nesting work correctly."""
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Set up a program with multiple levels of nesting
    context.set("private.level1", True)
    context.set("private.level2", True)
    context.set("private.level3", True)
    context.set("private.result", "initial")

    program = """
    if private.level1:
        private.result = "level1"
        if private.level2:
            private.result = "level2"
            if private.level3:
                private.result = "level3"
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check that the innermost conditional was reached
    assert context.get("private.result") == "level3"

    # Test different combinations of conditions
    test_cases = [
        # level1, level2, level3, expected result
        (True, True, False, "level2"),
        (True, False, True, "level1"),
        (True, False, False, "level1"),
        (False, True, True, "initial"),
        (False, False, True, "initial"),
        (False, False, False, "initial"),
    ]

    for level1, level2, level3, expected in test_cases:
        # Create a fresh context and interpreter for each test case
        context = RuntimeContext()
        interpreter = Interpreter(context)

        context.set("private.level1", level1)
        context.set("private.level2", level2)
        context.set("private.level3", level3)
        context.set("private.result", "initial")

        program = """
        if private.level1:
            private.result = "level1"
            if private.level2:
                private.result = "level2"
                if private.level3:
                    private.result = "level3"
        """

        result = parse(program)
        interpreter.execute_program(result)

        # Check the result
        assert context.get("private.result") == expected, f"Failed with levels {level1}, {level2}, {level3}"


def test_nested_conditionals_with_visitor():
    """Test that nested conditionals work with the visitor pattern."""
    context = RuntimeContext()

    # Create interpreter
    from opendxa.dana.runtime.interpreter import create_interpreter

    interpreter = create_interpreter(context)

    # Set up a program with nested conditionals
    context.set("private.outer", True)
    context.set("private.inner", True)
    context.set("private.result", "initial")

    program = """
    if private.outer:
        private.result = "outer"
        if private.inner:
            private.result = "inner"
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check that the innermost conditional was reached
    assert context.get("private.result") == "inner"
