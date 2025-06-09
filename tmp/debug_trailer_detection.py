#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def debug_trailer_detection():
    print("=== Debugging Trailer Detection During Parsing ===")

    # Patch the trailer method to see what's happening
    from opendxa.dana.sandbox.parser.transformer.expression_transformer import ExpressionTransformer

    original_trailer = ExpressionTransformer.trailer

    def debug_trailer(self, items):
        print(f"\n>>> TRAILER called with {len(items)} items:")
        for i, item in enumerate(items):
            print(f"  Item {i}: {type(item)} = {item}")
            if hasattr(item, "data"):
                print(f"    .data = {item.data}")
            if hasattr(item, "children"):
                print(f"    .children = {item.children}")
            if hasattr(item, "type"):
                print(f"    .type = {item.type}")
            if hasattr(item, "value"):
                print(f"    .value = {item.value}")

        result = original_trailer(self, items)
        print(f"<<< TRAILER result: {type(result)} = {result}")
        return result

    ExpressionTransformer.trailer = debug_trailer

    try:
        parser = DanaParser()

        test_cases = [
            "get_package_info",
            "get_package_info()",
            "factorial(4)",
            "utils.get_package_info()",
        ]

        for test_case in test_cases:
            print("\n" + "=" * 50)
            print(f"PARSING: {test_case}")
            print("=" * 50)

            try:
                ast = parser.parse(test_case)
                stmt = ast.statements[0]
                print("\nFINAL RESULT:")
                print(f"  Type: {type(stmt)}")
                print(f"  Node: {stmt}")
            except Exception as e:
                print(f"\nERROR: {e}")

    finally:
        # Restore original method
        ExpressionTransformer.trailer = original_trailer


if __name__ == "__main__":
    debug_trailer_detection()
