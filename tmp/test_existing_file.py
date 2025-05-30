#!/usr/bin/env python3
"""
Test existing Dana files to see if our grammar changes broke anything.
"""

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_existing_files():
    parser = DanaParser()

    files_to_test = [
        "examples/dana/na/basic_assignments.na",
        "examples/dana/na/builtin_functions_basic.na",
    ]

    for file_path in files_to_test:
        try:
            with open(file_path) as f:
                content = f.read()
            result = parser.parse(content, do_transform=False)
            print(f"✅ {file_path}: PASSED")
        except Exception as e:
            print(f"❌ {file_path}: FAILED - {e}")


if __name__ == "__main__":
    test_existing_files()
