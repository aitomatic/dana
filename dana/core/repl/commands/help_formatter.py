"""
Help message formatting for Dana REPL.

This module provides the HelpFormatter class that generates
help messages and displays available functions.
"""

from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme, print_header
from dana.core.repl.repl import REPL


class HelpFormatter(Loggable):
    """Formats and displays help information for the Dana REPL."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize with a REPL instance and color scheme."""
        super().__init__()
        self.repl = repl
        self.colors = colors

    def show_help(self) -> None:
        """Show comprehensive help information."""
        width = 80
        header_text = "Dana REPL HELP"
        print_header(header_text, width, self.colors)

        print(f"{self.colors.bold('Basic Commands:')}")
        print(f"  {self.colors.accent('help')}, {self.colors.accent('?')}         - Show this help message")
        print(f"  {self.colors.accent('exit')}, {self.colors.accent('quit')}      - Exit the REPL")

        print(f"\n{self.colors.bold('Special Commands:')}")
        print(f"  {self.colors.accent('##nlp on')}        - Enable natural language processing mode")
        print(f"  {self.colors.accent('##nlp off')}       - Disable natural language processing mode")
        print(f"  {self.colors.accent('##nlp status')}    - Check if NLP mode is enabled")
        print(f"  {self.colors.accent('##nlp test')}      - Test the NLP transcoder functionality")

        # Dynamic core functions listing
        print(f"\n{self.colors.bold('Core Functions:')}")
        self.show_core_functions()

        print(f"\n{self.colors.bold('Dana Syntax Basics:')}")
        print(f"  {self.colors.bold('Variables:')}      {self.colors.accent('private:x = 5')}, {self.colors.accent('public:data = hello')}")
        print(f"  {self.colors.bold('Conditionals:')}   {self.colors.accent('if private:x > 10:')}")
        print(f"                  {self.colors.accent('    log("Value is high", "info")')}")
        print(f"  {self.colors.bold('Loops:')}          {self.colors.accent('while private:x < 10:')}")
        print(f"                  {self.colors.accent('    private:x = private:x + 1')}")
        print(f"  {self.colors.bold('Functions:')}      {self.colors.accent('func add(a, b): return a + b')}")

        print(f"\n{self.colors.bold('Tips:')}")
        print(f"  {self.colors.accent('•')} Use {self.colors.bold('Tab')} for command completion")
        print(f"  {self.colors.accent('•')} Press {self.colors.bold('Ctrl+C')} to cancel current input")
        print(f"  {self.colors.accent('•')} Use {self.colors.bold('##')} on a new line to force execution of multiline block")
        print(f"  {self.colors.accent('•')} Multi-line mode automatically activates for incomplete statements")
        print(f"  {self.colors.accent('•')} Press {self.colors.bold('Enter')} on an empty line to execute multiline blocks")
        print(f"  {self.colors.accent('•')} Try describing actions in plain language when NLP mode is on")
        print()

    def show_core_functions(self) -> None:
        """Dynamically show available core functions from the function registry."""
        try:
            # Get the function registry from the REPL
            registry = self.repl.interpreter.function_registry

            # Get all functions in the local namespace (where core functions are registered)
            core_functions = registry.list("local")

            if not core_functions:
                print(f"  {self.colors.error('No core functions found')}")
                return

            # Sort functions for consistent display
            core_functions.sort()

            # Group functions by type/category for better organization
            printing_funcs = [f for f in core_functions if f in ["print"]]
            logging_funcs = [f for f in core_functions if f.startswith("log")]
            reasoning_funcs = [f for f in core_functions if f in ["reason"]]
            other_funcs = [f for f in core_functions if f not in printing_funcs + logging_funcs + reasoning_funcs]

            # Display functions by category
            if printing_funcs:
                print(f"  {self.colors.bold('Output:')}        ", end="")
                for i, func in enumerate(printing_funcs):
                    if i > 0:
                        print(", ", end="")
                    print(f"{self.colors.accent(func + '(...)')}", end="")
                print()

            if logging_funcs:
                print(f"  {self.colors.bold('Logging:')}       ", end="")
                for i, func in enumerate(logging_funcs):
                    if i > 0:
                        print(", ", end="")
                    print(f"{self.colors.accent(func + '(...)')}", end="")
                print()

            if reasoning_funcs:
                print(f"  {self.colors.bold('AI/Reasoning:')}  ", end="")
                for i, func in enumerate(reasoning_funcs):
                    if i > 0:
                        print(", ", end="")
                    print(f"{self.colors.accent(func + '(...)')}", end="")
                print()

            if other_funcs:
                print(f"  {self.colors.bold('Other:')}         ", end="")
                for i, func in enumerate(other_funcs):
                    if i > 0:
                        print(", ", end="")
                    print(f"{self.colors.accent(func + '(...)')}", end="")
                print()

            # Show function examples
            print(f"\n  {self.colors.bold('Function Examples:')}")
            if "print" in core_functions:
                print(f"    {self.colors.accent('print("Hello", "World", 123)')}    - Print multiple values")
            if "log" in core_functions:
                print(f"    {self.colors.accent('log("Debug info", "debug")')}      - Log with level")
            if "log_level" in core_functions:
                print(f"    {self.colors.accent('log_level("info")')}               - Set logging level")
            if "reason" in core_functions:
                print(f"    {self.colors.accent('reason("What is 2+2?")')}           - AI reasoning")

        except Exception as e:
            print(f"  {self.colors.error(f'Error listing core functions: {e}')}")
            # Fallback to hardcoded list
            print(
                f"  {self.colors.accent('print(...)')}, {self.colors.accent('log(...)')}, {self.colors.accent('log_level(...)')}, {self.colors.accent('reason(...)')}"
            )

    def show_nlp_status(self) -> None:
        """Show NLP mode status."""
        status = self.repl.get_nlp_mode()
        print(f"NLP mode: {self.colors.bold('✅ enabled') if status else self.colors.error('❌ disabled')}")
        has_transcoder = self.repl.transcoder is not None
        print(f"LLM resource: {self.colors.bold('✅ available') if has_transcoder else self.colors.error('❌ not available')}")

    def show_orphaned_else_guidance(self) -> None:
        """Show guidance for orphaned else statements."""
        print(f"{self.colors.error('Error:')} Orphaned 'else'/'elif' statement detected.")
        print("")
        print("To write if-else blocks, start with the if statement and use multiline mode:")
        print(f"  1. {self.colors.accent('Type the if statement (ends with :):')}")
        print("     >>> if condition:")
        print("     ...     # if body")
        print("     ... else:")
        print("     ...     # else body")
        print(f"     ... {self.colors.bold('[empty line to execute]')}")
        print("")
        print(f"  2. {self.colors.accent('Or start with ## to force multiline mode:')}")
        print("     >>> ##")
        print("     ... if condition:")
        print("     ...     # statements")
        print("     ... else:")
        print("     ...     # statements")
        print(f"     ... {self.colors.bold('[empty line to execute]')}")
        print("")
