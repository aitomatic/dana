#!/usr/bin/env python3
"""
DANA Command Line Interface

This script serves as the main entry point for the DANA language, similar to the python command.
It either starts the REPL when no arguments are provided, or executes a .na file when given.

Usage:
  dana                 Start the DANA REPL
  dana [file.na]       Execute a DANA file
  dana -h, --help      Show help message
"""

import argparse
import asyncio
import logging
import os
import sys

# Adjust path to import from the opendxa package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.common.exceptions import DanaError
from opendxa.dana.common.terminal_utils import ColorScheme, print_header, supports_color
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.log_manager import LogLevel, LogManager
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Initialize color scheme
colors = ColorScheme(supports_color())


def show_help():
    """Display help information."""
    print(f"{colors.header('DANA - Domain-Aware NeuroSymbolic Architecture')}")
    print("")
    print(f"{colors.bold('Usage:')}")
    print(f"  {colors.accent('dana')}                   Start the DANA REPL")
    print(f"  {colors.accent('dana [file.na]')}         Execute a DANA file")
    print(f"  {colors.accent('dana -h, --help')}        Show this help message")
    print(f"  {colors.accent('dana --debug')}           Enable debug logging")
    print("")


def execute_file(file_path, debug=False):
    """Execute a DANA file."""
    print_header(f"DANA Execution: {os.path.basename(file_path)}", colors=colors)

    try:
        with open(file_path) as f:
            program_source = f.read()
            print(f"{colors.accent(f'Loaded program source ({len(program_source)} bytes)')}")
    except Exception as e:
        print(f"{colors.error(f'Error reading file: {e}')}")
        sys.exit(1)

    # Create a context with an LLM resource
    context = SandboxContext()
    llm_resource = LLMResource()
    context.set("system.llm_resource", llm_resource)
    print(f"{colors.accent('Created execution context and initialized LLM resource')}")

    # Parse the program
    print("Parsing program...")
    parser = DanaParser()
    ast = parser.parse(program_source)
    print(f"{colors.accent('Program parsed successfully')}")

    # Initialize interpreter
    print("Initializing interpreter...")
    interpreter = DanaInterpreter(context=context)
    print(f"{colors.accent('Interpreter initialized')}")

    try:
        # Execute the program
        print("Executing program...")
        result = interpreter.execute_program(ast)
        print(f"{colors.accent('Program executed successfully')}")

        # Show final context state
        print(f"\n{colors.bold('--- Final Context State ---')}")
        print(f"{colors.accent(str(context))}")
        print(f"{colors.bold('---------------------------')}")

        # Get final result if available
        if result is not None:
            print(f"\n{colors.bold('Result:')} {colors.accent(str(result))}")

        print(f"\n{colors.bold('✓ Program execution completed successfully')}")

    except DanaError as e:
        print(f"\n{colors.error(f'DANA Error: {e}')}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{colors.error(f'Error executing DANA program: {e}')}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def start_repl(debug=False):
    """Start the DANA REPL."""
    # Import the REPL application module
    try:
        from opendxa.dana.repl.dana_repl_app import main as repl_main

        # Pass debug flag to repl_main
        await repl_main(debug=debug)
    except ImportError as e:
        print(f"{colors.error(f'Error: Failed to import REPL module: {e}')}")
        sys.exit(1)
    except Exception as e:
        print(f"{colors.error(f'Error starting REPL: {e}')}")
        sys.exit(1)


def main():
    """Main entry point for the DANA CLI."""
    parser = argparse.ArgumentParser(description="DANA Command Line Interface", add_help=False)  # We'll handle --help ourselves
    parser.add_argument("file", nargs="?", help="DANA file to execute (.na)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--force-color", action="store_true", help="Force colored output")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Handle color settings
    global colors
    if args.no_color:
        colors = ColorScheme(False)
    elif args.force_color:
        colors = ColorScheme(True)

    # Configure debug logging if requested
    if args.debug:
        print(f"{colors.accent('Debug logging enabled')}")
        # Configure the DXA_LOGGER for debug output
        DXA_LOGGER.configure(level=logging.DEBUG, console=True)
        # Set debug level using LogManager which is the recommended way
        LogManager.set_system_log_level(LogLevel.DEBUG)

    # Show help if requested
    if args.help:
        show_help()
        return

    # Check if a file was provided
    if args.file:
        # Make sure it has .na extension
        if not args.file.endswith(".na"):
            print(f"{colors.error('Error: File must have .na extension')}")
            print("")
            show_help()
            sys.exit(1)

        # Execute the file
        execute_file(args.file, debug=args.debug)
    else:
        # No file provided, start REPL
        asyncio.run(start_repl(debug=args.debug))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDANA execution interrupted by user")
        sys.exit(0)
