"""Runs DANA examples using the parser and interpreter.

Can run specific examples by passing their paths as command-line arguments.
If no arguments are given, runs all examples found in the 'code/' subdirectory.
"""

import glob
import os
import sys

# Adjust path to import from the opendxa package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from opendxa.dana.exceptions import DanaError
from opendxa.dana.io.file_io import read_dana_program
from opendxa.dana.language.ast import LogLevel
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter

# ANSI color codes
BLUE = "\033[94m"  # Program headers
GREEN = "\033[92m"  # Success messages
RED = "\033[91m"  # Errors
YELLOW = "\033[93m"  # Program output
CYAN = "\033[96m"  # DANA code/output
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text: str, color: str = BLUE):
    """Print a formatted header with color."""
    border = "=" * 60
    print(f"\n{color}{BOLD}{border}")
    print(text)
    print(f"{border}{RESET}\n")


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

    print_header(f"Running Example: {display_path}")

    try:
        # 1. Read
        print(f"{YELLOW}Reading from: {abs_example_path}{RESET}")
        dana_code = read_dana_program(abs_example_path)

        # 2. Parse
        print(f"{YELLOW}Parsing...{RESET}")
        parse_result = parse(dana_code)

        # 3. Setup Runtime
        print(f"{YELLOW}Initializing context and interpreter...{RESET}")
        context = RuntimeContext()
        interpreter = Interpreter(context=context)

        # Set log level to DEBUG for log_levels.dana example
        if os.path.basename(abs_example_path) == "log_levels.dana":
            interpreter.set_log_level(LogLevel.DEBUG)

        # 4. Interpret/Execute
        print(f"{YELLOW}Executing...{RESET}")
        interpreter.execute_program(parse_result)

        # 5. Show Result
        print(f"{GREEN}--- Final Context State ---{RESET}")
        print(f"{CYAN}{context}{RESET}")  # Uses the __str__ method of RuntimeContext
        print(f"{GREEN}---------------------------{RESET}")

    except FileNotFoundError:
        print(f"{RED}Error: Example file not found - {abs_example_path}{RESET}")
    except DanaError as e:
        print(f"{RED}DANA Error: {e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected Runtime Error: {e}{RESET}")
        import traceback

        traceback.print_exc()  # Print full stack trace for unexpected errors

    print_header(f"Finished Example: {display_path}", GREEN)


def find_examples():
    """Find all .dana files in the dana directory."""
    dana_dir = os.path.join(os.path.dirname(__file__), "code")
    example_paths = sorted(glob.glob(os.path.join(dana_dir, "*.dana")))
    return example_paths  # Returns paths relative to script location


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use provided command-line arguments as example paths
        examples_to_run_paths = sys.argv[1:]
        print(f"{YELLOW}Running specified examples: {examples_to_run_paths}{RESET}")

        # Validate paths
        examples = []
        for path in examples_to_run_paths:
            if not path.endswith(".dana"):
                print(f"{RED}Warning: Skipping non-.dana file: {path}{RESET}")
                continue
            if not os.path.exists(path):
                # Try resolving relative to the script's location if not found directly
                script_relative_path = os.path.join(os.path.dirname(__file__), path)
                if os.path.exists(script_relative_path):
                    examples.append(script_relative_path)
                else:
                    print(f"{RED}Warning: Example file not found: {path}{RESET}")
            else:
                examples.append(path)
    else:
        # Find all examples if no arguments are provided
        print(f"{YELLOW}Running all examples found in examples/dana/dana/...{RESET}")
        examples = find_examples()

    if not examples:
        print(f"{RED}No valid examples found or provided!{RESET}")
        sys.exit(1)

    print(f"\n{YELLOW}Found {len(examples)} examples to run:{RESET}")
    for example in examples:
        # Display the path relative to the CWD or just the basename for clarity
        abs_example_path = os.path.abspath(example)
        display_path = (
            os.path.relpath(abs_example_path)
            if os.path.commonpath([abs_example_path, os.getcwd()]) == os.getcwd()
            else os.path.basename(abs_example_path)
        )
        print(f"{GREEN}  - {display_path}{RESET}")
    print()

    for example in examples:
        run_example(example)
