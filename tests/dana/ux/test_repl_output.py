import io
import re
import sys

import pytest


def format_user_error(e, user_input):
    msg = str(e)
    if "Unexpected token" in msg:
        m = re.search(r"Unexpected token Token\('NAME', '([^']+)'\) at line (\d+), column (\d+)", msg)
        if m:
            token, line, col = m.groups()
            caret_line = " " * (int(col) - 1) + "^"
            return (
                f"Syntax Error:\n"
                f"  Input: {user_input}\n"
                f"         {caret_line}\n"
                f"  Unexpected '{token}' after condition. Did you forget a colon (:)?\n"
                f"  Tip: Use a colon after the condition, e.g., if x > 0:"
            )
        return f"Syntax Error:\n  {msg}"
    if "Undefined variable" in msg or "not defined" in msg:
        return (
            f"Name Error:\n"
            f"  Input: {user_input}\n"
            f"  Variable is not defined.\n"
            f"  Tip: Check for typos or define the variable before using it."
        )
    if "division by zero" in msg or "ZeroDivisionError" in msg:
        return (
            f"Math Error:\n"
            f"  Input: {user_input}\n"
            f"  Division by zero is not allowed.\n"
            f"  Tip: Check your divisor to avoid dividing by zero."
        )
    if "TypeError" in msg or "type mismatch" in msg:
        return f"Type Error:\n" f"  Input: {user_input}\n" f"  {msg}\n" f"  Tip: Ensure both operands are of compatible types."
    # Fallback
    return f"Error:\n  Input: {user_input}\n  {msg}"


def run_repl_and_capture_output(input_code):
    from opendxa.dana.repl.repl import REPL
    from opendxa.dana.sandbox.sandbox_context import SandboxContext

    repl = REPL(context=SandboxContext())
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        try:
            result = repl.execute(input_code)
            output = sys.stdout.getvalue()
            if result is not None:
                output += str(result)
        except Exception as e:
            output = format_user_error(e, input_code)
    finally:
        sys.stdout = old_stdout
    return output.strip()


@pytest.mark.parametrize(
    "input_code,expected_output",
    [
        ("private:x = 5", "5"),
        ("if x > 0 print('missing colon')", "Syntax Error:"),
    ],
)
def test_repl_output(input_code, expected_output, request):
    actual_output = run_repl_and_capture_output(input_code)
    if request.config.getoption("--ux-review"):
        print(f"\nInput:\n{input_code}\nOutput:\n{actual_output}\n")
    else:
        assert expected_output in actual_output
