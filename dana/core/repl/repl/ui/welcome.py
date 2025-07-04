"""
Welcome message display for Dana REPL.

This module provides the WelcomeDisplay class that shows
the welcome message and feature overview.
"""

from dana.common.terminal_utils import ColorScheme, print_header


class WelcomeDisplay:
    """Displays welcome messages and feature information for the Dana REPL."""

    def __init__(self, colors: ColorScheme):
        """Initialize with a color scheme."""
        self.colors = colors

    def show_welcome(self) -> None:
        """Show welcome message and help."""
        # Get terminal width for header
        width = 80

        # Use print_header utility
        print_header("Dana Interactive REPL", width, self.colors)

        print("\nWelcome to the Dana (Domain-Aware NeuroSymbolic Architecture) REPL!")
        print("Type Dana code or natural language commands and see them executed instantly.")
        print(
            f"Type {self.colors.bold('help')} or {self.colors.bold('?')} for help, {self.colors.bold('exit')} or {self.colors.bold('quit')} to end the session."
        )

        print(f"\n{self.colors.bold('Key Features:')}")
        print(f"  • {self.colors.accent('Multi-line Code Entry')} - Continue typing for blocks, prompt changes to '... '")
        print(f"  • {self.colors.accent('Press Enter on empty line')} - End multiline blocks and execute them")
        print(f"  • {self.colors.accent('Natural Language Processing')} - Enable with ##nlp on to use plain English")
        print(f"  • {self.colors.accent('Tab Completion')} - Press Tab to complete commands and keywords")
        print(f"  • {self.colors.accent('Command History')} - Use up/down arrows to navigate previous commands")
        print(f"  • {self.colors.accent('Syntax Highlighting')} - Colored syntax for better readability")
        print(f"  • {self.colors.accent('History Search')} - Press Ctrl+R to search command history")

        print(f"\n{self.colors.bold('Quick Commands:')}")
        print(f"  • {self.colors.accent('##')} - Force execution of multi-line block")
        print(f"  • {self.colors.accent('##nlp on/off')} - Toggle natural language processing mode")
        print(f"  • {self.colors.accent('Ctrl+C')} - Cancel the current input")

        print(f"\nType {self.colors.bold('help')} for full documentation\n")
