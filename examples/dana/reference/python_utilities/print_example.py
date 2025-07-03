"""Example demonstrating the DANA print statement."""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import dana
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter


def main():
    """Run the DANA print example."""
    print("Running DANA print example...\n")

    # Read the example file
    example_file = Path(__file__).parent / "na" / "print_example.na"
    with open(example_file) as f:
        code = f.read()

    # Parse the code
    print(f"Parsing code from {example_file}...\n")
    from dana.core.lang.parser.utils.parsing_utils import ParserCache

    parser = ParserCache.get_parser("dana")
    result = parser.parse(code, do_type_check=False)

    if not result.is_valid:
        print("Error parsing code:")
        for error in result.errors:
            print(f"  {error}")
        return

    # Create an interpreter and runtime context
    context = SandboxContext()
    interpreter = DanaInterpreter.new(context)

    # Enable debug logging to see all log messages
    os.environ["DANA_LOG_LEVEL"] = "DEBUG"

    # Execute the code
    print("Executing code...\n")
    interpreter.execute_program(result)

    print("\nDone!")


if __name__ == "__main__":
    main()
