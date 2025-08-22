"""
Help formatting for Dana REPL.

This module provides the HelpFormatter class that displays
comprehensive help information and status for the REPL.
"""

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

from dana.apps.repl.repl import REPL
from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme, print_header


class HelpFormatter(Loggable):
    """Formats and displays help information for the Dana REPL."""

    def __init__(self, repl: REPL, colors: ColorScheme):
        """Initialize with a REPL instance and color scheme."""
        super().__init__()
        self.repl = repl
        self.colors = colors

    def show_help(self) -> None:
        """Display comprehensive help information."""
        header_text = "Dana REPL Help"
        width = 80
        print_header(header_text, width, self.colors)

        print_formatted_text(ANSI(f"{self.colors.bold('Basic Commands:')}"))
        print_formatted_text(ANSI(f"  {self.colors.accent('help')}, {self.colors.accent('?')}         - Show this help message"))
        print_formatted_text(ANSI(f"  {self.colors.accent('exit')}, {self.colors.accent('quit')}      - Exit the REPL"))

        print_formatted_text(ANSI(f"\n{self.colors.bold('Special Commands:')}"))
        print_formatted_text(ANSI(f"  {self.colors.accent('/nlp on')}         - Enable natural language processing mode"))
        print_formatted_text(ANSI(f"  {self.colors.accent('/nlp off')}        - Disable natural language processing mode"))
        print_formatted_text(ANSI(f"  {self.colors.accent('/nlp status')}     - Check if NLP mode is enabled"))
        print_formatted_text(ANSI(f"  {self.colors.accent('/nlp test')}       - Test the NLP transcoder functionality"))
        print_formatted_text(ANSI(f"  {self.colors.accent('/status')}         - Show current REPL status and context information"))

        # Show core functions
        print_formatted_text(ANSI(f"\n{self.colors.bold('Core Functions:')}"))
        self._show_core_functions()

        print_formatted_text(ANSI(f"\n{self.colors.bold('Dana Syntax Basics:')}"))
        print_formatted_text(
            ANSI(
                f"  {self.colors.bold('Variables:')}      {self.colors.accent('private:x = 5')}, {self.colors.accent('public:data = hello')}"
            )
        )
        print_formatted_text(ANSI(f"  {self.colors.bold('Conditionals:')}   {self.colors.accent('if private:x > 10:')}"))
        print_formatted_text(ANSI(f"                  {self.colors.accent('    log("Value is high", "info")')}"))
        print_formatted_text(ANSI(f"  {self.colors.bold('Loops:')}          {self.colors.accent('while private:x < 10:')}"))
        print_formatted_text(ANSI(f"                  {self.colors.accent('    private:x = private:x + 1')}"))
        print_formatted_text(ANSI(f"  {self.colors.bold('Functions:')}      {self.colors.accent('func add(a, b): return a + b')}"))

        # Show tips and general info
        print_formatted_text(ANSI(f"\n{self.colors.bold('Tips:')}"))
        print_formatted_text(ANSI(f"  {self.colors.accent('•')} Use {self.colors.bold('Tab')} for command completion"))
        print_formatted_text(ANSI(f"  {self.colors.accent('•')} Press {self.colors.bold('Ctrl+C')} to cancel current input"))
        print_formatted_text(
            ANSI(f"  {self.colors.accent('•')} Use {self.colors.bold('/')} on a new line to force execution of multiline block")
        )
        print_formatted_text(ANSI(f"  {self.colors.accent('•')} Multi-line mode automatically activates for incomplete statements"))
        print_formatted_text(
            ANSI(f"  {self.colors.accent('•')} Press {self.colors.bold('Enter')} on an empty line to execute multiline blocks")
        )
        print_formatted_text(ANSI(f"  {self.colors.accent('•')} Try describing actions in plain language when NLP mode is on"))
        print_formatted_text(
            ANSI(f"  {self.colors.accent('•')} Promise objects are automatically detected and show meta info instead of resolving")
        )

    def _show_core_functions(self) -> None:
        """Display available core functions organized by category."""
        try:
            # Get all core functions from the registry
            registry = self.repl.interpreter.function_registry
            core_functions = registry.list_functions("system")

            if not core_functions:
                print_formatted_text(ANSI(f"  {self.colors.error('No core functions found')}"))
                return

            # Organize functions by category
            categories = {
                "Output": ["print", "old_reason", "reason", "context_aware_reason", "register_original_reason"],
                "Logging": ["log", "log_level"],
                "AI/Reasoning": ["llm", "reason", "old_reason", "context_aware_reason"],
                "Other": [],
            }

            # Categorize functions
            for func in core_functions:
                categorized = False
                for _, funcs in categories.items():
                    if func in funcs:
                        categorized = True
                        break
                if not categorized:
                    categories["Other"].append(func)

            # Display each category
            for category, funcs in categories.items():
                if funcs:
                    print_formatted_text(ANSI(f"  {self.colors.bold(category + ':')}        "), end="")
                    func_list = []
                    for func in funcs:
                        if func in core_functions:  # Only show if actually available
                            func_list.append(f"{self.colors.accent(func + '(...)')}")
                    if func_list:
                        print_formatted_text(ANSI(", ".join(func_list)))
                    else:
                        print_formatted_text(ANSI(""))

            # Show some example usages
            print_formatted_text(ANSI(f"\n  {self.colors.bold('Function Examples:')}"))
            # Show practical examples
            print_formatted_text(ANSI(f"    {self.colors.accent('print("Hello", "World", 123)')}    - Print multiple values"))
            # Show logging examples
            print_formatted_text(ANSI(f"    {self.colors.accent('log("Debug info", "debug")')}      - Log with level"))
            # Show more examples
            print_formatted_text(ANSI(f"    {self.colors.accent('log_level("info")')}               - Set logging level"))
            # Show reasoning example
            print_formatted_text(ANSI(f"    {self.colors.accent('reason("What is 2+2?")')}           - AI reasoning"))

        except Exception as e:
            print_formatted_text(ANSI(f"  {self.colors.error(f'Error listing core functions: {e}')}"))
            # Fallback list
            fallback = f"  {self.colors.accent('print(...)')}, {self.colors.accent('log(...)')}, {self.colors.accent('log_level(...)')}, {self.colors.accent('reason(...)')}"
            print_formatted_text(ANSI(fallback))

    def _show_core_functions_plain(self) -> None:
        """Display available core functions organized by category (plain text version for testing)."""
        try:
            # Get all core functions from the registry
            registry = self.repl.interpreter.function_registry
            core_functions = registry.list_functions("system")

            if not core_functions:
                print("  No core functions found")
                return

            # Organize functions by category
            categories = {
                "Output": ["print", "old_reason", "reason", "context_aware_reason", "register_original_reason"],
                "Logging": ["log", "log_level"],
                "AI/Reasoning": ["llm", "reason", "old_reason", "context_aware_reason"],
                "Other": [],
            }

            # Categorize functions
            for func in core_functions:
                categorized = False
                for _, funcs in categories.items():
                    if func in funcs:
                        categorized = True
                        break
                if not categorized:
                    categories["Other"].append(func)

            # Display each category
            for category, funcs in categories.items():
                if funcs:
                    print(f"  {category}:        ", end="")
                    func_list = []
                    for func in funcs:
                        if func in core_functions:  # Only show if actually available
                            func_list.append(f"{func}(...)")
                    if func_list:
                        print(", ".join(func_list))
                    else:
                        print("")

            # Show some example usages
            print("\n  Function Examples:")
            # Show practical examples
            print('    print("Hello", "World", 123)    - Print multiple values')
            # Show logging examples
            print('    log("Debug info", "debug")      - Log with level')
            # Show more examples
            print('    log_level("info")               - Set logging level')
            # Show reasoning example
            print('    reason("What is 2+2?")           - AI reasoning')

        except Exception as e:
            print(f"  Error listing core functions: {e}")
            # Fallback list
            print("  print(...), log(...), log_level(...), reason(...)")

    def show_core_functions(self) -> None:
        """Public method to display core functions (calls private _show_core_functions)."""
        self._show_core_functions()

    def show_core_functions_plain(self) -> None:
        """Public method to display core functions in plain text (for testing)."""
        self._show_core_functions_plain()

    def show_nlp_status(self) -> None:
        """Display current NLP status and configuration."""
        status = self.repl.get_nlp_mode()
        has_transcoder = self.repl.transcoder is not None

        print_formatted_text(ANSI(f"NLP mode: {self.colors.bold('✅ enabled') if status else self.colors.error('❌ disabled')}"))

        print_formatted_text(
            ANSI(f"LLM resource: {self.colors.bold('✅ available') if has_transcoder else self.colors.error('❌ not available')}")
        )

    def show_orphaned_else_guidance(self) -> None:
        """Show guidance for handling orphaned else/elif statements."""
        print_formatted_text(ANSI(f"{self.colors.error('Error:')} Orphaned 'else'/'elif' statement detected."))
        print_formatted_text(ANSI(""))
        print_formatted_text(ANSI(f"  1. {self.colors.accent('Type the if statement (ends with :):')}"))
        print_formatted_text(ANSI("     >>> if condition:"))
        print_formatted_text(ANSI("     ...     action1()"))
        print_formatted_text(ANSI("     >>> else:"))
        print_formatted_text(ANSI("     ...     action2()"))
        print_formatted_text(ANSI(f"     ... {self.colors.bold('[empty line to execute]')}"))
        print_formatted_text(ANSI(""))
        print_formatted_text(ANSI(f"  2. {self.colors.accent('Or start with / to force multiline mode:')}"))
        print_formatted_text(ANSI("     >>> /"))
        print_formatted_text(ANSI("     ... if condition:"))
        print_formatted_text(ANSI("     ...     action1()"))
        print_formatted_text(ANSI("     ... else:"))
        print_formatted_text(ANSI("     ...     action2()"))
        print_formatted_text(ANSI(f"     ... {self.colors.bold('[empty line to execute]')}"))
        print_formatted_text(ANSI(""))
