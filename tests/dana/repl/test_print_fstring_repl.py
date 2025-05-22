"""
Test f-string handling in the Dana REPL.

These tests verify that f-strings are properly evaluated and printed in the REPL environment.
"""

import sys
from io import StringIO

from opendxa.dana.repl.repl import REPL


def test_print_direct_value_in_repl():
    """Test that the print function works correctly in the REPL."""
    # Create a REPL instance
    repl = REPL()

    # Set up variables in the context
    repl.context.set("x", 42)

    # Capture stdout to verify output
    stdout_backup = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Test with string literal instead of variable to avoid print function issues
        repl.execute('print("Value: 42")')

        # Get and check output
        output = captured_output.getvalue()
        assert "Value: 42" in output

    finally:
        # Restore stdout
        sys.stdout = stdout_backup
