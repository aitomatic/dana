#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_debug_executor():
    print("=== Debugging Import Executor Logic ===")

    # Parse the from-import statement
    parser = DanaParser()
    interpreter = DanaInterpreter()

    # Parse and examine the AST
    program = parser.parse("from json import dumps as json_dumps", do_type_check=False, do_transform=True)

    print(f"Program: {program}")
    print(f"Statements: {program.statements}")

    import_stmt = program.statements[0]
    print(f"Import statement type: {type(import_stmt)}")
    print(f"Module: {import_stmt.module}")
    print(f"Names: {import_stmt.names}")

    # Examine the names structure
    for i, (name, alias) in enumerate(import_stmt.names):
        print(f"  Name {i}: '{name}' -> alias: '{alias}'")

    # Execute it and see what happens
    context = SandboxContext()
    result = interpreter.execute(program, context)

    print(f"\nExecution result: {result}")
    print(f"Context local scope: {context.get_scope('local')}")


if __name__ == "__main__":
    test_debug_executor()
