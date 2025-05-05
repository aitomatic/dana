"""Tests for while loops in DANA."""

from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter


def test_basic_while_loop():
    """Test that a basic while loop works correctly."""
    context = RuntimeContext()
    interpreter = Interpreter(context)
    
    # Set up a program with a while loop
    context.set("private.counter", 0)
    context.set("private.result", "initial")
    
    program = """
    while private.counter < 5:
        private.result = "iteration " + private.counter
        private.counter = private.counter + 1
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check that the loop ran the correct number of times
    assert context.get("private.counter") == 5
    assert context.get("private.result") == "iteration 4"


def test_nested_while_loops():
    """Test that nested while loops work correctly."""
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Set up a program with nested while loops
    context.set("private.outer", 0)
    context.set("private.inner", 0)
    context.set("private.result", "initial")
    
    program = """
    while private.outer < 3:
        private.result = "outer " + private.outer
        private.inner = 0
        while private.inner < 2:
            private.result = "inner " + private.inner
            private.inner = private.inner + 1
        private.outer = private.outer + 1
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check the final state
    assert context.get("private.outer") == 3
    assert context.get("private.inner") == 2
    assert context.get("private.result") == "inner 1"


def test_while_with_conditionals():
    """Test that while loops with conditionals work correctly."""
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Set up a program with a while loop containing a conditional
    context.set("private.counter", 0)
    context.set("private.result", "initial")
    
    program = """
    while private.counter < 5:
        if private.counter % 2 == 0:
            private.result = "even " + private.counter
        private.counter = private.counter + 1
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check the final state
    assert context.get("private.counter") == 5
    assert context.get("private.result") == "even 4"


def test_conditionals_with_while():
    """Test that conditionals with while loops work correctly."""
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Set up a program with a conditional containing a while loop
    context.set("private.run_loop", True)
    context.set("private.counter", 0)
    context.set("private.result", "initial")
    
    program = """
    if private.run_loop:
        while private.counter < 3:
            private.result = "counter " + private.counter
            private.counter = private.counter + 1
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check the final state
    assert context.get("private.counter") == 3
    assert context.get("private.result") == "counter 2"

    # Test with run_loop = False
    context = RuntimeContext()
    interpreter = Interpreter(context)
    
    context.set("private.run_loop", False)
    context.set("private.counter", 0)
    context.set("private.result", "initial")
    
    interpreter.execute_program(result)
    
    # Check that the loop didn't run
    assert context.get("private.counter") == 0
    assert context.get("private.result") == "initial"


def test_while_with_visitor_pattern():
    """Test that while loops work with the visitor pattern."""
    context = RuntimeContext()
    
    # Create interpreter
    from opendxa.dana.runtime.interpreter import create_interpreter
    interpreter = create_interpreter(context)

    # Set up a program with a while loop
    context.set("private.counter", 0)
    context.set("private.result", "initial")
    
    program = """
    while private.counter < 3:
        private.result = "iteration " + private.counter
        private.counter = private.counter + 1
    """

    result = parse(program)
    interpreter.execute_program(result)

    # Check the final state
    assert context.get("private.counter") == 3
    assert context.get("private.result") == "iteration 2"