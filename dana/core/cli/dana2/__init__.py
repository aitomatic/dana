import argparse
import sys

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext

from .dana_input_args_parser import parse_dana_input_args

def main():
    """
    CLI entry point for running a Dana .na script with input arguments.
    Usage: dana2 <file.na> [key1=val1 key2=val2 ...]
    """
    parser = argparse.ArgumentParser(description="Run a Dana .na script with input arguments.")
    parser.add_argument("file", type=str, help="Path to the .na file to execute")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("inputs", nargs=argparse.REMAINDER, help="Input arguments as key=value pairs")
    args = parser.parse_args()

    # Parse input arguments into a dictionary
    input_dict = parse_dana_input_args(args.inputs)

    # Prepare a SandboxContext and inject input variables into local scope
    context = SandboxContext()
    for key, value in input_dict.items():
        context.set(key, value)

    # Run the Dana script with the prepared context
    result = DanaSandbox.quick_run(args.file, debug_mode=args.debug, context=context)

    # Print the result
    print(result)
