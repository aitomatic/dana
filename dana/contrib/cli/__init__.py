import argparse
from pathlib import Path

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext
from dana.util.env import load_dana_env

from .dana_input_args_parser import parse_dana_input_args

def main():
    """
    CLI entry point for running a Dana .na script with input arguments.
    Usage: dana2 <file.na> [key1=val1 key2=val2 ...]
    """
    arg_parser = argparse.ArgumentParser(description="Run a Dana .na script with input arguments.")
    arg_parser.add_argument("file_path", type=str, help="Path to the .na file to execute")
    arg_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    arg_parser.add_argument("inputs", nargs=argparse.REMAINDER, help="Input arguments as key=value pairs")
    args = arg_parser.parse_args()

    # Parse input arguments into a dictionary
    input_dict = parse_dana_input_args(args.inputs)

    # Prepare a SandboxContext and inject input variables into local scope
    context = SandboxContext()
    for key, value in input_dict.items():
        context.set(key, value)

    load_dana_env(dot_env_file_path=Path(args.file_path).parent / '.env')

    # Run the Dana script with the prepared context
    DanaSandbox.quick_run(file_path=args.file_path, debug_mode=args.debug, context=context)
