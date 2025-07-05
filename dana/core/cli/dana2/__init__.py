import argparse
import sys

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext

from .dana_input_args_parser import parse_dana_input_args

def dana2():
    """
    CLI entry point for running a Dana .na script with input arguments.
    Usage: python -m dana.core.cli.dana2.__init__ <file.na> [key1=val1 key2=val2 ...]
    """
    parser = argparse.ArgumentParser(description="Run a Dana .na script with input arguments.")
    parser.add_argument("file", type=str, help="Path to the .na file to execute")
    parser.add_argument("inputs", nargs=argparse.REMAINDER, help="Input arguments as key=value pairs")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    file_path = args.file
    input_args = tuple(args.inputs)
    debug = args.debug

    # Parse input arguments into a dictionary
    input_dict = parse_dana_input_args(input_args)

    # Prepare a SandboxContext and inject input variables into local scope
    context = SandboxContext()
    for key, value in input_dict.items():
        context.set(key, value)

    # Run the Dana script with the prepared context
    result = DanaSandbox.quick_run(file_path, debug_mode=debug, context=context)

    # Print output and result
    if result.success:
        if result.output:
            print(result.output)
        print(f"Result: {result.result}")
    else:
        print(f"Error: {result.error}")
        sys.exit(1)
