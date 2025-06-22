#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser

code = """
struct Data:
    value: str

def process(data: Data, as_string: bool = true) -> str | int:
    if as_string:
        return data.value
    else:
        try:
            return int(data.value)
        except:
            return 0

local:data = Data(value="42")
local:as_string = data.process()
local:as_int = data.process(as_string=false)
"""

print("Parsing code to examine AST structure...")
parser = DanaParser()
result = parser.parse(code)

print(f"Parse successful: {result.success}")
if result.success and result.ast:
    program = result.ast
    print(f"Number of program statements: {len(program.statements)}")

    for i, stmt in enumerate(program.statements):
        print(f"\nStatement {i}: {type(stmt).__name__}")
        if hasattr(stmt, "name") and hasattr(stmt.name, "name"):
            print(f"  Name: {stmt.name.name}")
        if hasattr(stmt, "body"):
            print(f"  Body statements: {len(stmt.body)}")
            for j, body_stmt in enumerate(stmt.body):
                print(f"    Body[{j}]: {type(body_stmt).__name__}")
                if hasattr(body_stmt, "target") and hasattr(body_stmt.target, "name"):
                    print(f"      Target: {body_stmt.target.name}")
else:
    print(f"Parse failed: {result.error}")
