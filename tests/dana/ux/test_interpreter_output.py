import re

import pytest


def format_user_error(e, user_input):
    msg = str(e)
    # Remove parser internals
    msg = "\n".join(line for line in msg.splitlines() if "Expected one of" not in line and "Previous tokens" not in line)
    # Try to extract line/column info
    line_col = re.search(r"line (\d+), col(?:umn)? (\d+)", msg)
    line_col_str = f" (line {line_col.group(1)}, col {line_col.group(2)})" if line_col else ""
    if "Unexpected token" in msg:
        token = re.search(r"Unexpected token Token\('NAME', '([^']+)'\)", msg)
        token_str = f"'{token.group(1)}'" if token else "input"
        return f"Syntax Error{line_col_str}: Unexpected {token_str} after condition. Did you forget a colon?"
    if "No terminal matches" in msg:
        return "Syntax Error: Unexpected or misplaced token."
    if "unsupported expression type" in msg.lower() or "not supported" in msg.lower():
        return "Execution Error: Invalid or unsupported expression."
    if "Undefined variable" in msg or "is not defined" in msg:
        var = re.search(r"'([^']+)'", msg)
        var_str = var.group(1) if var else "variable"
        return f"Name Error: '{var_str}' is not defined."
    if "must be accessed with a scope prefix" in msg:
        return "Name Error: Variable must be accessed with a scope prefix (e.g., private:x)."
    if "TypeError" in msg or "unsupported operand" in msg:
        return "Type Error: Invalid operation."
    if "SyntaxError" in msg or "syntax error" in msg:
        return "Syntax Error: Invalid syntax."
    if "Execution Error" in msg:
        return msg
    return f"Error: {msg.strip()}"


# Example function to run interpreter and capture output (replace with your actual runner)
def run_and_capture_output(input_code):
    from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
    from opendxa.dana.sandbox.parser.dana_parser import DanaParser
    from opendxa.dana.sandbox.sandbox_context import SandboxContext

    context = SandboxContext()
    interpreter = DanaInterpreter()
    parser = DanaParser()
    try:
        try:
            ast = parser.parse(input_code)
            result = interpreter.execute_program(ast, context)
            output = interpreter.get_and_clear_output()
            if result is not None:
                if output:
                    output += "\n" + str(result)
                else:
                    output = str(result)
        except Exception as e:
            output = format_user_error(e, input_code)
    finally:
        pass
    return output.strip()


# Example test cases (add more as needed)
@pytest.mark.parametrize(
    "input_code,expected_output",
    [
        ("if x > 0 print('missing colon')", "Syntax Error"),
        ("if private:x > 0:\n    print('ok')\nelse:\n    print('fail')", "Syntax Error"),
        ("print('hello') print('world')", "Syntax Error"),
        ("print(does_not_exist)", "Error accessing variable"),
        ("private:x = 'foo' + 5", "Syntax Error"),
        ("private:x = 1 / 0", "division by zero"),
        ("private:x = 42", "42"),  # Success
        ("print('hello world')", "Syntax Error"),
    ],
)
def test_user_output(input_code, expected_output, request):
    actual_output = run_and_capture_output(input_code)
    # If output starts with 'Error:', re-route through format_user_error
    if actual_output.startswith("Error:"):
        actual_output = format_user_error(actual_output, input_code)
    # Check for line length
    for line in actual_output.splitlines():
        assert len(line) <= 120, f"Output line too long: {line}"
    assert expected_output in actual_output
