#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
"""
Code → Execution (end-to-end) tests for the DANA interpreter.

These tests parse and execute DANA code strings, covering the full language pipeline:
- Assignment & Scoping
- Literals
- Arithmetic & Operator Precedence
- Comparisons & Logical Ops
- Control Flow (if/elif/else, while, for)
- Functions
- Strings & Collections
- Comments & Whitespace
- Error Handling
- Import & Scope Keywords
"""

import pytest

from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def run_dana_code(code):
    parser = DanaParser()
    program = parser.parse(code, do_type_check=True, do_transform=True)
    interpreter = Interpreter(SandboxContext())
    interpreter.execute_program(program)
    return interpreter.context


# --- Assignment & Scoping ---
def test_assignment_and_scopes():
    ctx = run_dana_code("private:x = 1\npublic:y = 2\nz = 3")
    assert ctx.get("private.x") == 1
    assert ctx.get("public.y") == 2
    assert ctx.get("local.z") == 3  # default scope


# --- Literals ---
def test_literals():
    ctx = run_dana_code('a = 42\nb = 3.14\nc = "hello"\nd = True\ne = None\nf = [1,2,3]\ng = {"a":1}\nh = (1,2)')
    assert ctx.get("local.a") == 42
    assert ctx.get("local.b") == 3.14
    assert ctx.get("local.c") == "hello"
    assert ctx.get("local.d") is True
    assert ctx.get("local.e") is None
    assert ctx.get("local.f") == [1, 2, 3]
    assert ctx.get("local.g") == {"a": 1}
    assert ctx.get("local.h") == (1, 2)


# --- Arithmetic & Operator Precedence ---
def test_arithmetic_operators():
    ctx = run_dana_code("x = 2 + 3\ny = 5 - 1\nz = 2 * 3\nw = 8 / 2\nv = 7 % 4\nu = 2 ^ 3")
    assert ctx.get("local.x") == 5
    assert ctx.get("local.y") == 4
    assert ctx.get("local.z") == 6
    assert ctx.get("local.w") == 4
    assert ctx.get("local.v") == 3
    assert ctx.get("local.u") == 8


def test_operator_precedence():
    ctx = run_dana_code("x = 2 + 3 * 4\ny = (2 + 3) * 4\nz = 2 ^ 3 * 2\nw = 2 * 3 ^ 2")
    assert ctx.get("local.x") == 14
    assert ctx.get("local.y") == 20
    assert ctx.get("local.z") == 16
    assert ctx.get("local.w") == 18


# --- Comparisons & Logical Ops ---
def test_comparisons_and_logical():
    ctx = run_dana_code(
        "a = 2 < 3\nb = 2 == 2\nc = 2 != 3\nd = 2 >= 2\ne = 2 <= 3\nf = 2 > 1\ng = True and False\nh = True or False\ni = not False"
    )
    assert ctx.get("local.a") is True
    assert ctx.get("local.b") is True
    assert ctx.get("local.c") is True
    assert ctx.get("local.d") is True
    assert ctx.get("local.e") is True
    assert ctx.get("local.f") is True
    assert ctx.get("local.g") is False
    assert ctx.get("local.h") is True
    assert ctx.get("local.i") is True


# --- Control Flow ---
def test_if_else_elif():
    code = """
x = 1
if x > 0:
    y = 10
elif x == 0:
    y = 20
else:
    y = 30
"""
    ctx = run_dana_code(code)
    assert ctx.get("local.y") == 10


def test_while_loop_integration():
    code = """
x = 0
while x < 3:
    x = x + 1
"""
    ctx = run_dana_code(code)
    assert ctx.get("local.x") == 3


def test_for_loop():
    code = """
sum = 0
for i in [1,2,3]:
    sum = sum + i
"""
    ctx = run_dana_code(code)
    assert ctx.get("local.sum") == 6


# --- Functions ---
@pytest.mark.skip(reason="FunctionDefinition not yet implemented")
def test_function_def_and_call():
    code = """
def add(a, b):
    return a + b
x = add(2, 3)
"""
    ctx = run_dana_code(code)
    assert ctx.get("local.x") == 5


# --- Strings & Collections ---
def test_fstring_and_multiline_string():
    code = 'x = f"hello {42}"\ny = """multi\\nline"""'
    ctx = run_dana_code(code)
    assert "hello" in ctx.get("local.x")
    assert "multi" in ctx.get("local.y")


# --- Comments & Whitespace ---
def test_comments_and_whitespace():
    code = """
# this is a comment
x = 1  # inline comment
"""
    ctx = run_dana_code(code)
    assert ctx.get("local.x") == 1


# --- Error Handling ---
def test_assert_and_raise():
    code = """
x = 1
assert x == 1
"""
    ctx = run_dana_code(code)
    assert ctx.get("local.x") == 1
    # Test raise
    code = "raise 'error'"
    parser = DanaParser()
    program = parser.parse(code, do_type_check=True, do_transform=True)
    interpreter = Interpreter(SandboxContext())
    try:
        interpreter.execute_program(program)
    except Exception as e:
        assert "error" in str(e) or "raise" in str(e)


# --- Import & Scope Keywords ---
def test_scope_keywords():
    code = "private:x = 1\npublic:y = 2\nsystem:z = 3\nlocal:w = 4"
    ctx = run_dana_code(code)
    assert ctx.get("private.x") == 1
    assert ctx.get("public.y") == 2
    assert ctx.get("system.z") == 3
    assert ctx.get("local.w") == 4
