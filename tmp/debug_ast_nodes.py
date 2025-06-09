#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def debug_ast_nodes():
    print("=== Debugging AST Node Generation ===")

    parser = DanaParser()

    # Test variable access
    print("1. Variable access AST:")
    var_ast = parser.parse("get_package_info")
    print(f"   Type: {type(var_ast.statements[0])}")
    print(f"   Node: {var_ast.statements[0]}")
    if hasattr(var_ast.statements[0], "name"):
        print(f"   Name: {var_ast.statements[0].name}")

    # Test function call
    print("\n2. Function call AST:")
    func_ast = parser.parse("get_package_info()")
    print(f"   Type: {type(func_ast.statements[0])}")
    print(f"   Node: {func_ast.statements[0]}")
    if hasattr(func_ast.statements[0], "name"):
        print(f"   Name: {func_ast.statements[0].name}")
    if hasattr(func_ast.statements[0], "args"):
        print(f"   Args: {func_ast.statements[0].args}")

    # Test assignment with function call
    print("\n3. Assignment with function call AST:")
    assign_ast = parser.parse("result = get_package_info()")
    print(f"   Type: {type(assign_ast.statements[0])}")
    print(f"   Node: {assign_ast.statements[0]}")
    if hasattr(assign_ast.statements[0], "value"):
        print(f"   Value type: {type(assign_ast.statements[0].value)}")
        print(f"   Value: {assign_ast.statements[0].value}")
        if hasattr(assign_ast.statements[0].value, "name"):
            print(f"   Value name: {assign_ast.statements[0].value.name}")


if __name__ == "__main__":
    debug_ast_nodes()
