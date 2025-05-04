"""Runs DANA examples using the parser and interpreter.

Can run specific examples by passing their paths as command-line arguments.
If no arguments are given, runs all examples found in the 'dana/' subdirectory.
"""

import glob
import os
import sys

# Adjust path to import from the opendxa package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from opendxa.dana.exceptions import DanaError
from opendxa.dana.io.file_io import read_dana_program
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.state.context import RuntimeContext


def run_example(example_path: str):
    """Reads, parses, and executes a DANA example file."""
    # Ensure we are using an absolute path for reading
    abs_example_path = os.path.abspath(example_path)

    # Display the path relative to the CWD or just the basename for clarity
    display_path = (
        os.path.relpath(abs_example_path)
        if os.path.commonpath([abs_example_path, os.getcwd()]) == os.getcwd()
        else os.path.basename(abs_example_path)
    )

    print(f"\n{'=' * 60}")
    print(f"Running Example: {display_path}")
    print(f"{'=' * 60}\n")

    try:
        # 1. Read
        print(f"Reading from: {abs_example_path}")
        dana_code = read_dana_program(abs_example_path)
        print("--- Code ---")
        print(dana_code)
        print("------------")

        # 2. Parse
        print("Parsing...")
        parse_result = parse(dana_code)

        # 3. Setup Runtime
        print("Initializing context and interpreter...")
        context = RuntimeContext()
        interpreter = Interpreter(context=context)

        # 4. Interpret/Execute
        print("Executing...")
        interpreter.execute_program(parse_result)

        # 5. Show Result
        print("--- Final Context State ---")
        print(context)  # Uses the __str__ method of RuntimeContext
        print("---------------------------")

    except FileNotFoundError:
        print(f"Error: Example file not found - {abs_example_path}")
    except DanaError as e:
        print(f"DANA Error: {e}")
    except Exception as e:
        print(f"Unexpected Runtime Error: {e}")
        import traceback

        traceback.print_exc()  # Print full stack trace for unexpected errors

    print(f"\n{'=' * 60}")
    print(f"Finished Example: {display_path}")
    print(f"{'=' * 60}\n")


def find_examples():
    """Find all .dana files in the dana directory."""
    dana_dir = os.path.join(os.path.dirname(__file__), "dana")
    example_paths = sorted(glob.glob(os.path.join(dana_dir, "*.dana")))
    return example_paths  # Returns paths relative to script location


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use provided command-line arguments as example paths
        examples_to_run_paths = sys.argv[1:]
        print(f"Running specified examples: {examples_to_run_paths}")

        # Validate paths
        examples = []
        for path in examples_to_run_paths:
            if not path.endswith(".dana"):
                print(f"Warning: Skipping non-.dana file: {path}")
                continue
            if not os.path.exists(path):
                # Try resolving relative to the script's location if not found directly
                script_relative_path = os.path.join(os.path.dirname(__file__), path)
                if os.path.exists(script_relative_path):
                    examples.append(script_relative_path)
                else:
                    print(f"Warning: Example file not found: {path}")
            else:
                examples.append(path)
    else:
        # Find all examples if no arguments are provided
        print("Running all examples found in examples/dana/dana/...")
        examples = find_examples()

    if not examples:
        print("No valid examples found or provided!")
        sys.exit(1)

    print(f"\nFound {len(examples)} examples to run:")
    for example in examples:
        # Display the path relative to the CWD or just the basename for clarity
        abs_example_path = os.path.abspath(example)
        display_path = (
            os.path.relpath(abs_example_path)
            if os.path.commonpath([abs_example_path, os.getcwd()]) == os.getcwd()
            else os.path.basename(abs_example_path)
        )
        print(f"  - {display_path}")
    print()

    for example in examples:
        run_example(example)
