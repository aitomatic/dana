#!/usr/bin/env python3

import traceback

from opendxa.dana import DanaSandbox


def test_import():
    print("=== Testing Import Implementation ===")

    sandbox = DanaSandbox()

    try:
        print("Testing: import math")
        result = sandbox.eval("import math")
        print(f"Success! Result: {result}")
        print(f"Result type: {type(result)}")

        # Try to access math after import
        print("\nTesting: math.pi after import")
        result2 = sandbox.eval("math.pi")
        print(f"Math.pi result: {result2}")

    except Exception as e:
        print(f"Exception: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print("Traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    test_import()
