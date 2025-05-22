#!/usr/bin/env python3
"""
Diagnostic script to verify function registry initialization and function resolution
"""

import logging
from pathlib import Path

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.repl.repl import REPL
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.interpreter.functions.core.register_core_functions import register_core_functions
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.log_manager import LogLevel, LogManager
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DiagnosticLogger(Loggable):
    """Simple diagnostic logging class."""

    def __init__(self):
        """Initialize the logger."""
        super().__init__(logger_name="opendxa.dana.diagnostics")


def print_separator(text):
    """Print a separator with text."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80 + "\n")


def main():
    """Run the diagnostics."""
    # Set up logging - this is essential to see debug messages
    # Configure the DXA_LOGGER first
    DXA_LOGGER.configure(level=logging.DEBUG, console=True)
    # Then set the Dana log level using LogManager
    LogManager.set_system_log_level(LogLevel.DEBUG)

    # Create a diagnostic logger
    logger = DiagnosticLogger()
    logger.debug("Diagnostic script started")

    # 1. Check core directory and available functions
    print_separator("1. CHECKING CORE DIRECTORY")
    core_dir = Path("opendxa/dana/sandbox/interpreter/functions/core")
    print(f"Core directory: {core_dir}")
    print("Files in core directory:")
    for f in core_dir.glob("*.py"):
        print(f"  {f.name}")

    # 2. Create a function registry directly and verify registration
    print_separator("2. TESTING DIRECT FUNCTION REGISTRY")
    registry = FunctionRegistry()
    logger.debug("Created new FunctionRegistry")

    # Register core functions
    register_core_functions(registry)
    logger.debug("Registered core functions")

    # List registered functions
    print("Registered functions:")
    for ns in ["local", "private", "public", "system"]:
        funcs = registry.list(namespace=ns)
        print(f"  {ns}: {funcs}")

    # Try direct resolution of print and reason
    print("\nDirect function resolution:")
    try:
        print_func, func_type, metadata = registry.resolve("print")
        print(f"  print() resolved: {print_func}, type: {func_type}")
    except Exception as e:
        print(f"  Error resolving print(): {e}")

    try:
        reason_func, func_type, metadata = registry.resolve("reason")
        print(f"  reason() resolved: {reason_func}, type: {func_type}")
    except Exception as e:
        print(f"  Error resolving reason(): {e}")

    # 3. Check interpreter initialization and function registry
    print_separator("3. CHECKING INTERPRETER INITIALIZATION")
    context = SandboxContext()
    interpreter = DanaInterpreter(context)
    logger.debug("Created DanaInterpreter")

    # Access function_registry property to ensure initialization
    registry = interpreter.function_registry
    logger.debug("Accessed interpreter.function_registry")

    # List registered functions from interpreter
    print("Functions registered in interpreter:")
    for ns in ["local", "private", "public", "system"]:
        funcs = registry.list(namespace=ns)
        print(f"  {ns}: {funcs}")

    # 4. Check REPL initialization
    print_separator("4. CHECKING REPL INITIALIZATION")
    repl = REPL(llm_resource=LLMResource())
    logger.debug("Created REPL")

    # Access interpreter and function registry from REPL
    print("REPL interpreter and registry:")
    print(f"  REPL has interpreter: {hasattr(repl, 'interpreter')}")
    print(f"  Interpreter has function_registry: {hasattr(repl.interpreter, 'function_registry')}")
    if hasattr(repl.interpreter, "function_registry"):
        registry = repl.interpreter.function_registry
        print("  Functions registered in REPL:")
        for ns in ["local", "private", "public", "system"]:
            funcs = registry.list(namespace=ns)
            print(f"    {ns}: {funcs}")

    # 5. Test function resolution in expression context
    print_separator("5. TESTING FUNCTION RESOLUTION IN EXPRESSION")

    # Parse simple programs that use print and reason
    parser = DanaParser()
    logger.debug("Created DanaParser")

    print_program = 'print("Hello")'
    reason_program = 'reason("test")'

    # Parse and execute print
    print(f"\nParsing and executing: {print_program}")
    try:
        parse_result = parser.parse(print_program)
        print("  Parsing succeeded")

        # Inspect the AST to see function calls
        if hasattr(parse_result, "program"):
            program = parse_result.program
            print(f"  Program type: {type(program).__name__}")
            print(f"  Program statements: {len(program.statements)}")
            for stmt in program.statements:
                print(f"  Statement type: {type(stmt).__name__}")

        # Try to execute (may fail)
        try:
            repl.execute(print_program)
            print("  Execution succeeded")
        except Exception as e:
            print(f"  Execution failed: {e}")

    except Exception as e:
        print(f"  Parsing failed: {e}")

    # Parse and execute reason
    print(f"\nParsing and executing: {reason_program}")
    try:
        parse_result = parser.parse(reason_program)
        print("  Parsing succeeded")

        # Try to execute (may fail)
        try:
            repl.execute(reason_program)
            print("  Execution succeeded")
        except Exception as e:
            print(f"  Execution failed: {e}")

    except Exception as e:
        print(f"  Parsing failed: {e}")

    # 6. Check context state
    print_separator("6. CHECKING CONTEXT STATE")
    print("Context state:")
    print(f"  system.function_registry exists: {repl.context.has('system.function_registry')}")
    if repl.context.has("system.function_registry"):
        registry = repl.context.get("system.function_registry")
        print(f"  Registry type: {type(registry).__name__}")

    # Done
    logger.debug("Diagnostic script completed")


if __name__ == "__main__":
    main()
