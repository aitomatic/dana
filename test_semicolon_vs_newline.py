#!/usr/bin/env python3
"""
Test script to compare semicolon vs newline execution paths.
Run this to see the debug output for both cases.
"""

import os
import sys

# Add the dana directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dana"))

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.log_manager import LogLevel


def test_execution_paths():
    """Test both semicolon and newline execution paths."""

    # Create sandbox with debug logging
    sandbox = DanaSandbox(debug_mode=True)

    # Set log level to DEBUG to see all the debug messages
    from dana.core.lang.log_manager import SandboxLogger

    SandboxLogger.set_system_log_level(LogLevel.DEBUG, sandbox.context)

    print("=" * 60)
    print("TESTING NEWLINE PATH")
    print("=" * 60)

    # Test newline path
    newline_code = """agent Nanda
Nanda.chat("hello")"""

    print(f"Input:\n{repr(newline_code)}")
    print("-" * 40)

    try:
        result = sandbox.execute_string(newline_code)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("TESTING SEMICOLON PATH")
    print("=" * 60)

    # Test semicolon path
    semicolon_code = 'agent Nanda ; Nanda.chat("hello")'

    print(f"Input:\n{repr(semicolon_code)}")
    print("-" * 40)

    try:
        result = sandbox.execute_string(semicolon_code)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_execution_paths()
