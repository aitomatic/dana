#!/usr/bin/env python3
"""
Adana Command Line Interface - Main Entry Point

Simple CLI router that decides whether to:
- Execute a Python script
- Launch the interactive REPL

Usage:
  adana                    Start Dana conversational agent
  adana script.py          Execute a Python script
  adana-repl               Start interactive Python REPL
  adana --help             Show help message
"""

import argparse
from pathlib import Path
import sys


def main():
    """Main entry point for the Adana CLI."""
    parser = argparse.ArgumentParser(
        description="Adana - Domain-Aware Neurosymbolic Agent Framework",
        add_help=False,
    )
    parser.add_argument("file", nargs="?", help="Python script to execute")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    parser.add_argument("--version", action="store_true", help="Show version")

    args = parser.parse_args()

    # Show help
    if args.help:
        show_help()
        return 0

    # Show version
    if args.version:
        from adana import __version__

        print(f"Adana {__version__}")
        return 0

    # Execute file or start REPL
    if args.file:
        return execute_file(args.file)
    else:
        return start_repl()


def show_help():
    """Display help information."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  Adana - Domain-Aware Neurosymbolic Agent Framework       ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  adana                    Start Dana conversational agent
  adana-repl               Start interactive Python REPL
  adana script.py          Execute a Python script
  adana --help             Show this help message
  adana --version          Show version information

Dana is a conversational AI that helps you manage agents, resources,
and workflows through natural language interaction.

Use 'adana-repl' for a Python REPL with pre-imported Adana classes.
""")


def execute_file(file_path: str) -> int:
    """Execute a Python script.

    Args:
        file_path: Path to the Python script to execute

    Returns:
        Exit code (0 for success, 1 for error)
    """
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File '{file_path}' not found")
        return 1

    if not path.suffix == ".py":
        print("Error: File must have .py extension")
        return 1

    try:
        # Read and execute the file
        code = path.read_text()
        exec(code, {"__name__": "__main__", "__file__": str(path)})
        return 0
    except Exception as e:
        print(f"Error executing script: {e}")
        import traceback

        traceback.print_exc()
        return 1


def start_repl() -> int:
    """Start the Dana conversational agent.

    Returns:
        Exit code (0 for success)
    """
    try:
        from adana.apps.dana.__main__ import main as dana_main

        dana_main()
        return 0
    except ImportError as e:
        print(f"Error: Failed to import Dana module: {e}")
        return 1
    except Exception as e:
        print(f"Error starting Dana: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
