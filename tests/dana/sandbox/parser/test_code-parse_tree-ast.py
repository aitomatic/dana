#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
import textwrap

import pytest

from opendxa.dana.sandbox.parser.ast import Conditional, FunctionCall, FunctionDefinition, Program, TryBlock, WhileLoop
from opendxa.dana.sandbox.parser.dana_parser import DanaParser

CODE_SAMPLES = {
    "nested_if_elif_else": """
    if x > 0:
        log.setLevel("DEBUG")
        if y < 0:
            z = 1
            log.error("y is negative")
        else:
            z = 2
            log.error("y is non-negative")
    elif x == 0:
        z = 3
        log.setLevel("INFO")
    else:
        z = 4
        log.error("x is not positive")
    """,
    "while_for_function": """
    while n > 0:
        n = n - 1
        log.setLevel("TRACE")
        for i in [1,2,3]:
            total = total + i
            log.error("iteration", i)
    def foo(a, b):
        log.setLevel("WARN")
        if a > b:
            log.error("a > b")
            return a
        else:
            log.error("a <= b")
            return b
    """,
    "try_except_finally": """
    try:
        risky()
        log.setLevel("ERROR")
    except (ErrorType):
        handle()
        log.error("exception occurred")
    finally:
        cleanup()
        log.setLevel("INFO")
    """,
    "combined_program": """
    def main():
        log.setLevel("INFO")
        for user in users:
            if user.is_active:
                try:
                    process(user)
                    log.setLevel("DEBUG")
                except (ProcessError):
                    log.error("failed to process user")
    """,
    "agentic_workflow": """
    # Agentic workflow example
    topic = get_topic_from_user()
    user_input = f"Summarize the latest news about {topic}"
    abc = reason(user_input)
    if abc:
        log.setLevel("INFO")
        log.error(f"Agent returned: {abc}")
    else:
        log.setLevel("ERROR")
        log.error("No response from agent.")
    """,
}


def parse_and_get_program(code, do_transform=True, do_type_check=False):
    parser = DanaParser()
    return parser.parse(textwrap.dedent(code), do_type_check=do_type_check, do_transform=do_transform)


def find_function_call_recursive(body, name):
    if isinstance(body, list):
        for item in body:
            if find_function_call_recursive(item, name):
                return True
    elif isinstance(body, FunctionCall):
        return getattr(body, "name", None) == name
    elif hasattr(body, "body"):
        if find_function_call_recursive(body.body, name):
            return True
    elif hasattr(body, "statements"):
        if find_function_call_recursive(body.statements, name):
            return True
    elif hasattr(body, "children"):
        if find_function_call_recursive(body.children, name):
            return True
    # Check for Assignment or nodes with 'value' attribute
    if hasattr(body, "value"):
        if find_function_call_recursive(body.value, name):
            return True
    return False


def assert_function_calls_in_ast(ast, sample_name):
    if sample_name == "nested_if_elif_else":
        stmt = ast.statements[0]
        assert isinstance(stmt, Conditional)
        assert find_function_call_recursive(stmt.body, "local.log.setLevel")
    elif sample_name == "while_for_function":
        while_stmt = ast.statements[0]
        assert isinstance(while_stmt, WhileLoop)
        assert find_function_call_recursive(while_stmt.body, "local.log.setLevel")
    elif sample_name == "try_except_finally":
        try_stmt = ast.statements[0]
        assert isinstance(try_stmt, TryBlock)
        assert find_function_call_recursive(try_stmt.body, "local.log.setLevel")
    elif sample_name == "combined_program":
        func = ast.statements[0]
        assert isinstance(func, FunctionDefinition)
        assert find_function_call_recursive(func.body, "local.log.setLevel")
    elif sample_name == "agentic_workflow":
        # Check for assignment to 'abc' and a FunctionCall to 'local.reason'
        assignments = [s for s in ast.statements if hasattr(s, "target") and getattr(s.target, "name", None) == "local.abc"]
        assert assignments, "No assignment to abc found"
        assert find_function_call_recursive(ast.statements, "local.reason"), "No call to local.reason() found"


# Add a fixture for the typecheck flag
@pytest.fixture(params=[True, False], ids=["typecheck_on", "typecheck_off"])
def typecheck_flag(request):
    return request.param


@pytest.mark.parametrize(
    "sample_name,do_transform", [(name, False) for name in CODE_SAMPLES.keys()] + [(name, True) for name in CODE_SAMPLES.keys()]
)
def test_program_samples(sample_name, do_transform, typecheck_flag):
    if typecheck_flag and do_transform:
        pytest.xfail("Integration samples are not type-safe; undefined names are expected.")
    code = CODE_SAMPLES[sample_name]
    result = parse_and_get_program(code, do_transform=do_transform, do_type_check=typecheck_flag)
    if not do_transform:
        assert hasattr(result, "data")  # Should be a Lark Tree
    else:
        assert isinstance(result, Program)
        assert_function_calls_in_ast(result, sample_name)
