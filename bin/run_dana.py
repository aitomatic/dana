#!/usr/bin/env python3
"""
Simple script to run a DANA program.
"""

import inspect
import sys

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.repl.repl import REPL
from opendxa.dana.sandbox.interpreter.functions.core import reason_function


def main():
    """Run a DANA program from a file."""
    if len(sys.argv) != 2:
        print("Usage: python run_dana.py <dana_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        with open(file_path) as f:
            program_source = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Print debug info about the reason function
    print(f"Reason function signature: {inspect.signature(reason_function.reason_function)}")

    try:
        # Initialize REPL with LLM resource
        repl = REPL(llm_resource=LLMResource())

        # Get a reference to the original reason function
        original_reason = reason_function.reason_function

        # Create a wrapper that fixes parameter order
        def fixed_reason_wrapper(*args, **kwargs):
            print(f"Fixed wrapper called with args: {args}, kwargs: {kwargs}")

            # Check parameter order and fix if needed
            if len(args) >= 2:
                # If first arg is SandboxContext and second is str, swap them
                if isinstance(args[0], type(repl.context)) and isinstance(args[1], str):
                    print("Swapping context and prompt parameters")
                    # Create new args with swapped parameters
                    new_args = (args[1], args[0]) + args[2:]
                    print(f"New args: {new_args}")
                    return original_reason(*new_args, **kwargs)

            # If we get here, no swapping was needed, or we're not sure how to handle
            # Let's make sure the parameters are in the right types
            print(f"Parameter types: {[type(a) for a in args]}")

            # Try to fix the parameters if needed
            if len(args) >= 1:
                # First parameter should be the prompt (string)
                prompt = args[0]
                if not isinstance(prompt, str):
                    if hasattr(prompt, "value"):
                        print(f"Converting prompt from {type(prompt)} to string using value attribute")
                        prompt = prompt.value
                    else:
                        print(f"Converting prompt from {type(prompt)} to string using str()")
                        prompt = str(prompt)

                # Second parameter should be the context
                context = args[1] if len(args) >= 2 else repl.context

                # Rest of the parameters
                other_args = args[2:] if len(args) > 2 else ()

                print(f"Calling with fixed parameters: prompt={prompt}, context={context}")
                return original_reason(prompt, context, *other_args, **kwargs)

            # Just try with the original parameters
            return original_reason(*args, **kwargs)

        # Monkey patch the reason function
        reason_function.reason_function = fixed_reason_wrapper

        # Execute the program
        result = repl.execute(program_source)

        if result is not None:
            print(f"Result: {result}")
    except Exception as e:
        print(f"Error executing DANA program: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
