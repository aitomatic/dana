#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_simple_parser():
    print("=== Testing Simple Parser ===")

    parser = DanaParser()

    # Test cases
    test_cases = [
        "from json import dumps",
        "from json import dumps as json_dumps",
        "from math import sqrt as square_root",
    ]

    for case in test_cases:
        print(f"\nTesting: {case}")
        try:
            program = parser.parse(case, do_type_check=False, do_transform=True)
            import_stmt = program.statements[0]
            print(f"  Module: {import_stmt.module}")
            print(f"  Names: {import_stmt.names}")

            for i, (name, alias) in enumerate(import_stmt.names):
                print(f"    Name {i}: '{name}' -> alias: '{alias}'")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_simple_parser()
