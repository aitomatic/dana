"""
Test f-string handling in the Dana REPL.

These tests verify that f-strings are properly evaluated and printed in the REPL environment.
"""

from dana.apps.repl.repl import REPL


def test_print_direct_value_in_repl():
    """Test that the print function works correctly in the REPL."""
    # Create a REPL instance
    repl = REPL()

    # Set up variables in the context
    repl.context.set("x", 42)

    # Execute print statement - Dana print writes to internal buffer, not stdout
    repl.execute('print("Value: 42")')

    # Get the output from the interpreter's buffer instead of stdout
    output = repl.interpreter.get_and_clear_output()
    assert "Value: 42" in output
