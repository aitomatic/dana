#!/usr/bin/env python3
"""
Enable the new function call implementation components.

This script safely enables the new function call implementation
by setting the feature flags in relevant classes:

1. ExpressionEvaluator._use_arg_processor = True
2. DanaFunction._use_adapter = True
3. PythonFunction._use_adapter = True

Run this script after implementing and testing the new components.
"""

import sys
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))


def enable_new_implementation(enable=True):
    """
    Enable or disable the new function call implementation.

    Args:
        enable: Whether to enable (True) or disable (False) the new implementation
    """
    # Import the modules
    try:
        from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
        from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction
        from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
        from opendxa.dana.sandbox.interpreter.functions.python_function import PythonFunction
        from opendxa.dana.sandbox.interpreter.interpreter import Interpreter

        # Check if the new implementation components are available
        try:
            from opendxa.dana.sandbox.interpreter.functions.argument_processor import ArgumentProcessor
            from opendxa.dana.sandbox.interpreter.functions.function_adapter import DanaFunctionAdapter, PythonFunctionAdapter

            # Set the feature flags
            ExpressionEvaluator._use_arg_processor = enable
            DanaFunction._use_adapter = enable
            PythonFunction._use_adapter = enable

            # Enable in function registry for all current and future instances
            FunctionRegistry._use_arg_processor = enable

            # Also update the registry in any active interpreters
            # This ensures existing instances will use the new implementation too
            Interpreter._function_registry_use_arg_processor = enable

            print(f"{'Enabled' if enable else 'Disabled'} new function call implementation")
            print(f"- ArgumentProcessor: {'Available' if 'ArgumentProcessor' in locals() else 'Not available'}")
            print(f"- Function adapters: {'Available' if 'DanaFunctionAdapter' in locals() else 'Not available'}")
            print(f"- ExpressionEvaluator._use_arg_processor = {ExpressionEvaluator._use_arg_processor}")
            print(f"- DanaFunction._use_adapter = {DanaFunction._use_adapter}")
            print(f"- PythonFunction._use_adapter = {PythonFunction._use_adapter}")
            print(f"- FunctionRegistry._use_arg_processor = {FunctionRegistry._use_arg_processor}")

            return True
        except ImportError as e:
            print(f"ERROR: New implementation components not available: {str(e)}")
            return False

    except ImportError as e:
        print(f"ERROR: Could not import required modules: {str(e)}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Enable/disable new function call implementation")
    parser.add_argument("--disable", action="store_true", help="Disable the new implementation")

    args = parser.parse_args()

    enable_new_implementation(not args.disable)


if __name__ == "__main__":
    main()
