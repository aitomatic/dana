#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_parse_tree():
    print("=== Testing Parse Tree ===")

    parser = DanaParser()

    # Test cases
    test_cases = [
        "from json import dumps",
        "from json import dumps as json_dumps",
    ]

    for case in test_cases:
        print(f"\nTesting: {case}")
        try:
            # Parse WITHOUT transformation to see raw parse tree
            tree = parser.parse(case, do_type_check=False, do_transform=False)
            print(f"Raw tree: {tree}")
            print(f"Tree pretty: {tree.pretty()}")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_parse_tree()
