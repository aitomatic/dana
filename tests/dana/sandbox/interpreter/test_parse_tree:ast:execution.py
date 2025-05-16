#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
"""
ParseTree → AST → Execution tests for the DANA interpreter.

These tests parse code to an AST, then execute it using the interpreter.
"""

from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_arithmetic_assignment_parse_tree_ast_execution():
    """Test assignment of an arithmetic expression via code → AST → execution."""
    code = "private:result = 2 + 3"
    parser = DanaParser()
    program = parser.parse(code, do_transform=True)
    interpreter = Interpreter(SandboxContext())
    interpreter.execute_program(program)
    assert interpreter.context.get("private.result") == 5
